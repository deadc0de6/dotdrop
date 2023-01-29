#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6
#
# test bad diff cmd
# returns 1 in case of error
#

# exit on first error
set -e

# all this crap to get current path
rl="readlink -f"
if ! ${rl} "${0}" >/dev/null 2>&1; then
  rl="realpath"

  if ! hash ${rl}; then
    echo "\"${rl}\" not found !" && exit 1
  fi
fi
cur=$(dirname "$(${rl} "${0}")")

#hash dotdrop >/dev/null 2>&1
#[ "$?" != "0" ] && echo "install dotdrop to run tests" && exit 1

#echo "called with ${1}"

# dotdrop path can be pass as argument
ddpath="${cur}/../"
[ "${1}" != "" ] && ddpath="${1}"
[ ! -d "${ddpath}" ] && echo "ddpath \"${ddpath}\" is not a directory" && exit 1

export PYTHONPATH="${ddpath}:${PYTHONPATH}"
bin="python3 -m dotdrop.dotdrop"
if hash coverage 2>/dev/null; then
  bin="coverage run -p --source=dotdrop -m dotdrop.dotdrop"
fi

echo "dotdrop path: ${ddpath}"
echo "pythonpath: ${PYTHONPATH}"

# get the helpers
# shellcheck source=tests-ng/helpers
source "${cur}"/helpers

echo -e "$(tput setaf 6)==> RUNNING $(basename "${BASH_SOURCE[0]}") <==$(tput sgr0)"

################################################################
# this is the test
################################################################
basedir=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
echo "[+] dotdrop dir: ${basedir}"

clear_on_exit "${basedir}"

# create the config file
cfg="${basedir}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  diff_command: xxxxxxxxx {0} {1}
dotfiles:
profiles:
_EOF

set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}"
[ "$?" = "0" ] && exit 1

out=$(cd "${ddpath}" | ${bin} compare -c "${cfg}")
echo "${out}" | grep -i 'traceback' && exit 1

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  diff_command:
dotfiles:
profiles:
_EOF

set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}"
[ "$?" = "0" ] && exit 1

out=$(cd "${ddpath}" | ${bin} compare -c "${cfg}")
echo "${out}" | grep -i 'traceback' && exit 1

echo "OK"
exit 0
