#!/usr/bin/env bash
# author: jtt9340 (https://github.com/jtt9340)
#
# test install cmpignore with negative ignores globally
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

# dotdrop path can be pass as argument
ddpath="${cur}/../"
[ -n "${1}" ] && ddpath="${1}"
[ ! -d "${ddpath}" ] && echo "ddpath \"{ddpath}\" is not a directory" && exit 1

export PYTHONPATH="${ddpath}:${PYTHONPATH}"
bin="python3 -m dotdrop.dotdrop"
if hash coverage 2>/dev/null; then
  bin="coverage run -a --source=dotdrop -m dotdrop.dotdrop"
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
basedir=$(mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d)
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"

# the dotfile to be imported
tmpd=$(mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d)

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

# some files
mkdir -p "${tmpd}"/{program,config}
touch "${tmpd}"/program/a
touch "${tmpd}"/config/a

# create the config file
cfg="${basedir}/config.yaml"
create_conf "${cfg}" # sets token

# import
echo "[+] import"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/program
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/config

# add files
echo "[+] add files"
touch "${tmpd}"/program/b
touch "${tmpd}"/config/b

# adding ignore in dotfile
cfg2="${basedir}/config2.yaml"
sed '/dotpath: dotfiles/a\
\ \ cmpignore:\
\ \ \ \ - "*/config/*"\
\ \ \ \ - "!*/config/a"\
' "${cfg}" > "${cfg2}"
cat "${cfg2}"

# expects one diff
echo "[+] comparing with ignore in dotfile - 1 diff"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg2}" --verbose
[ "$?" = "0" ] && exit 1
set -e

echo "OK"
exit 0
