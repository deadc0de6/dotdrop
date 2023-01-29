#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test install to temp
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

# dotdrop directory
basedir=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${basedir}"/dotfiles
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${basedir}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_x:
    src: x
    dst: ${tmpd}/x
  f_y:
    src: y
    dst: ${tmpd}/y
    link: link
  f_z:
    src: z
    dst: ${tmpd}/z
profiles:
  p1:
    dotfiles:
    - f_x
    - f_y
    - f_z
_EOF

echo 'test_x' > "${basedir}"/dotfiles/x
echo 'test_y' > "${basedir}"/dotfiles/y
echo "00000000  01 02 03 04 05" | xxd -r - "${basedir}"/dotfiles/z

echo "[+] install"
log="${basedir}/log"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 --showdiff --verbose --temp > "${log}"

tmpfile=$(cat "${basedir}"/log | grep 'installed to tmp ' | sed 's/^.*to tmp "\(.*\)"./\1/')
echo "tmpfile: ${tmpfile}"
clear_on_exit "${tmpfile}"

cat "${log}" | grep '^3 dotfile(s) installed.$'
[ "$?" != "0" ] && exit 1

echo "OK"
exit 0
