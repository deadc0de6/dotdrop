#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6
#
# test dotpath templated
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

dotpath="xyz"

# dotdrop directory
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/${dotpath}
echo "[+] dotdrop dir: ${tmps}"
echo "[+] dotpath dir: ${tmps}/${dotpath}"

# dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

echo "content" > "${tmps}"/${dotpath}/abc

# create the config file
cfg="${tmps}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: "{{@@ env['DOTDROP_DOTPATH'] @@}}"
dotfiles:
  f_abc:
    src: abc
    dst: ${tmpd}/abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

echo "[+] install"
export DOTDROP_DOTPATH=${dotpath}
cd "${ddpath}" | ${bin} install -c "${cfg}" -f -p p1 --verbose | grep '^1 dotfile(s) installed.$'
[ "$?" != "0" ] && exit 1

[ ! -e "${tmpd}"/abc ] && echo "f_abc not installed" && exit 1

# clean
rm "${tmpd}"/abc

# create the config file
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: "{{@@ var1 @@}}"
variables:
  var1: "${dotpath}"
dotfiles:
  f_abc:
    src: abc
    dst: ${tmpd}/abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

echo "[+] install"
cd "${ddpath}" | ${bin} install -c "${cfg}" -f -p p1 --verbose | grep '^1 dotfile(s) installed.$'
[ "$?" != "0" ] && exit 1

[ ! -e "${tmpd}"/abc ] && echo "f_abc not installed" && exit 1

echo "OK"
exit 0
