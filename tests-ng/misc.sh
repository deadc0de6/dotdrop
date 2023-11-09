#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6
#
# test misc stuff
# returns 1 in case of error
#

## start-cookie
set -eu -o errtrace -o pipefail
cur=$(cd "$(dirname "${0}")" && pwd)
ddpath="${cur}/../"
PPATH="{PYTHONPATH:-}"
export PYTHONPATH="${ddpath}:${PPATH}"
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

echo "content" > "${basedir}"/dotfiles/x

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
  f_fake:
    src:
    dst:
profiles:
  p1:
    dotfiles:
    - f_x
  p2:
    dotfiles:
  p3:
    dotfiles:
    - f_fake
_EOF

echo "[+] compare - does not exist on dst"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1 --verbose
[ "$?" = "0" ] && exit 1
set -e

echo "[+] install - no dotfiles"
set +e
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p2 --verbose
[ "$?" = "0" ] && exit 1
set -e

echo "[+] compare - no dotfiles"
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p2 --verbose
[ "$?" != "0" ] && exit 1

echo "[+] compare - fake dotfile"
cd "${ddpath}" | ${bin} compare -w1 -c "${cfg}" -p p3 --verbose
[ "$?" != "0" ] && exit 1

echo "[+] compare - fake dotfile"
cd "${ddpath}" | ${bin} compare -w3 -c "${cfg}" -p p3 --verbose
[ "$?" != "0" ] && exit 1

set +e
echo "[+] update - bad profile"
cd "${ddpath}" | ${bin} update -c "${cfg}" -p p4 --verbose
[ "$?" = "0" ] && exit 1
set -e

echo "[+] grepable profiles"
cd "${ddpath}" | ${bin} profiles -c "${cfg}" --grepable --verbose
[ "$?" != "0" ] && exit 1

echo "[+] files - bad profile but return 0"
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p10 --verbose
[ "$?" != "0" ] && exit 1

echo "[+] detail - bad profile but return 0"
cd "${ddpath}" | ${bin} detail -c "${cfg}" -p p10 --verbose
[ "$?" != "0" ] && exit 1

echo "[+] remove - no dotfiles"
cd "${ddpath}" | ${bin} remove -c "${cfg}" -p p2 --verbose
[ "$?" != "0" ] && exit 1

echo "OK"
exit 0
