#!/usr/bin/env bash
# author: jtt9340 (https://github.com/jtt9340)
#
# test install negative ignore absolute/relative
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
basedir=$(mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d)
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"

# the dotfile to be imported
tmpd=$(mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d)

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

# some files
mkdir -p "${tmpd}"/program/ignore_me
echo "some data" > "${tmpd}"/program/a
echo "some data" > "${tmpd}"/program/ignore_me/b
echo "some data" > "${tmpd}"/program/ignore_me/c

# create the config file
cfg="${basedir}/config.yaml"
create_conf "${cfg}" # sets token

# import
echo "[+] import"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/program

# adding ignore in dotfile
cfg2="${basedir}/config2.yaml"
sed '/d_program:/a\
\ \ \ \ instignore:\
\ \ \ \ - "*/ignore_me/*"\
\ \ \ \ - "!*/ignore_me/c"
' "${cfg}" > "${cfg2}"

# install
rm -rf "${tmpd}"
echo "[+] install with negative ignore in dotfile"
cd "${ddpath}" | ${bin} install -c "${cfg2}" --verbose
[ "$?" != "0" ] && exit 1
echo '(1) expect structure to be
.
└── program
 ├── a
 └── ignore_me
    └── c'

[[ -n "$(find "${tmpd}"/program -name a)" ]] || exit 1
echo "(1) found program/a ... good"
[[ -n "$(find "${tmpd}"/program/ignore_me -name b)" ]] && exit 1
echo "(1) didn't find program/b ... good"
[[ -n "$(find "${tmpd}"/program/ignore_me -name c)" ]] || exit 1
echo "(1) found program/c ... good"

echo "OK"
exit 0

