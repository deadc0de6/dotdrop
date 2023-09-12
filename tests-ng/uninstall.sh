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
# dotdrop directory
basedir=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${basedir}"/dotfiles
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

echo "modified" > "${basedir}"/dotfiles/x

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
profiles:
  p1:
    dotfiles:
    - f_x
_EOF

#########################
## no original
#########################

# install
echo "[+] install (1)"
cd "${ddpath}" | ${bin} install -c "${cfg}" -f -p p1 --verbose | grep '^1 dotfile(s) installed.$'
[ "$?" != "0" ] && exit 1
[ ! -e "${tmpd}"/x ] && echo "f_x not installed" && exit 1
grep 'modified' "${tmpd}"/x

# uninstall
echo "[+] uninstall"
cd "${ddpath}" | ${bin} uninstall -c "${cfg}" -f -p p1 --verbose
[ "$?" != "0" ] && exit 1
[ -e "${tmpd}"/x ] && echo "f_x not installed" && exit 1

#########################
## with original
#########################
echo 'original' > "${tmpd}"/x

# install
echo "[+] install (2)"
cd "${ddpath}" | ${bin} install -c "${cfg}" -f -p p1 --verbose | grep '^1 dotfile(s) installed.$'
[ "$?" != "0" ] && exit 1
[ ! -e "${tmpd}"/x ] && echo "f_x not installed" && exit 1
grep 'modified' "${tmpd}"/x

# uninstall
echo "[+] uninstall"
cd "${ddpath}" | ${bin} uninstall -c "${cfg}" -f -p p1 --verbose
[ "$?" != "0" ] && exit 1
[ -e "${tmpd}"/x ] && echo "f_x not installed" && exit 1
grep 'original' "${tmpd}"/x

# TODO handle directory

echo "OK"
exit 0
