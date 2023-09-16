#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6
#
# test uninstall (no symlink)
# returns 1 in case of error
#

## start-cookie
set -e
cur=$(cd "$(dirname "${0}")" && pwd)
ddpath="${cur}/../"
export PYTHONPATH="${ddpath}:${PYTHONPATH}"
altbin="python3 -m dotdrop.dotdrop"
if hash coverage 2>/dev/null; then
  mkdir -p coverages/
  altbin="coverage run -p --data-file coverages/coverage --source=dotdrop -m dotdrop.dotdrop"
fi
bin="${DT_BIN:-${altbin}}"
# shellcheck source=tests-ng/helpers
source "${cur}"/helpers
echo -e "$(tput setaf 6)==> RUNNING $(basename "${BASH_SOURCE[0]}") <==$(tput sgr0)"
## end-cookie

################################################################
# this is the test
################################################################

# $1 pattern
# $2 path
grep_or_fail()
{
  grep "${1}" "${2}" >/dev/null 2>&1 || (echo "pattern \"${1}\" not found in ${2}" && exit 1)
}

# dotdrop directory
basedir=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${basedir}"/dotfiles
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

echo "modified" > "${basedir}"/dotfiles/x
mkdir -p "${basedir}"/dotfiles/y
echo "modified" > "${basedir}"/dotfiles/y/file

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
  d_y:
    src: y
    dst: ${tmpd}/y
profiles:
  p1:
    dotfiles:
    - f_x
    - d_y
_EOF

#########################
## no original
#########################

# install
echo "[+] install (1)"
cd "${ddpath}" | ${bin} install -c "${cfg}" -f -p p1 --verbose | grep '^2 dotfile(s) installed.$'

# tests
[ ! -e "${tmpd}"/x ] && echo "f_x not installed" && exit 1
[ ! -e "${tmpd}"/y/file ] && echo "d_y not installed" && exit 1
grep_or_fail 'modified' "${tmpd}"/x
grep_or_fail 'modified' "${tmpd}"/y/file

# uninstall
echo "[+] uninstall (1)"
cd "${ddpath}" | ${bin} uninstall -c "${cfg}" -f -p p1 --verbose
[ "$?" != "0" ] && exit 1

# tests
[ -e "${tmpd}"/x ] && echo "f_x not uninstalled" && exit 1
[ -d "${tmpd}"/y ] && echo "d_y not uninstalled" && exit 1
[ -e "${tmpd}"/y/file ] && echo "d_y file not uninstalled" && exit 1

#########################
## with original
#########################
echo 'original' > "${tmpd}"/x
mkdir -p "${tmpd}"/y
echo "original" > "${tmpd}"/y/file

# install
echo "[+] install (2)"
cd "${ddpath}" | ${bin} install -c "${cfg}" -f -p p1 --verbose | grep '^2 dotfile(s) installed.$'

# tests
[ ! -e "${tmpd}"/x ] && echo "f_x not installed" && exit 1
[ ! -d "${tmpd}"/y ] && echo "d_y not installed" && exit 1
[ ! -e "${tmpd}"/y/file ] && echo "d_y file not installed" && exit 1
grep_or_fail 'modified' "${tmpd}"/x
grep_or_fail 'modified' "${tmpd}"/y/file

# uninstall
echo "[+] uninstall (2)"
cd "${ddpath}" | ${bin} uninstall -c "${cfg}" -f -p p1 --verbose
[ "$?" != "0" ] && exit 1

# tests
[ ! -e "${tmpd}"/x ] && echo "f_x backup not restored" && exit 1
[ ! -d "${tmpd}"/y ] && echo "d_y backup not restored" && exit 1
[ ! -e "${tmpd}"/y/file ] && echo "d_y backup not restored" && exit 1
grep_or_fail 'original' "${tmpd}"/x
grep_or_fail 'original' "${tmpd}"/y/file

echo "OK"
exit 0
