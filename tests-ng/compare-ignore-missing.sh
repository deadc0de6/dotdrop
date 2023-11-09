#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test compare ignore
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
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"
dt="${basedir}/dotfiles"
mkdir -p "${dt}"/folder
touch "${dt}"/folder/a

# the dotfile to be imported
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

# some files
cp -r "${dt}"/folder "${tmpd}"/
mkdir -p "${tmpd}"/folder
touch "${tmpd}"/folder/b
mkdir "${tmpd}"/folder/c

# create the config file
cfg="${basedir}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: false
  create: true
  dotpath: dotfiles
dotfiles:
  thedotfile:
    dst: ${tmpd}/folder
    src: folder
profiles:
  p1:
    dotfiles:
    - thedotfile
_EOF

#
# Test with no ignore-missing setting
#

# Expect diff
echo "[+] test with no ignore-missing setting"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" --verbose --profile=p1
[ "$?" = "0" ] && exit 1
set -e

#
# Test with command-line flga
#

# Expect no diff
echo "[+] test with command-line flag"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" --verbose --profile=p1 --ignore-missing
[ "$?" != "0" ] && exit 1
set -e

#
# Test with global option
#

cat > "${cfg}" << _EOF
config:
  backup: false
  create: true
  dotpath: dotfiles
  ignore_missing_in_dotdrop: true
dotfiles:
  thedotfile:
    dst: ${tmpd}/folder
    src: folder
profiles:
  p1:
    dotfiles:
    - thedotfile
_EOF

# Expect no diff
echo "[+] test global option"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" --verbose --profile=p1
[ "$?" != "0" ] && exit 1
set -e

#
# Test with dotfile option
#

cat > "${cfg}" << _EOF
config:
  backup: false
  create: true
  dotpath: dotfiles
dotfiles:
  thedotfile:
    dst: ${tmpd}/folder
    src: folder
    ignore_missing_in_dotdrop: true
profiles:
  p1:
    dotfiles:
    - thedotfile
_EOF

# Expect no diff
echo "[+] test dotfile option"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" --verbose --profile=p1
[ "$?" != "0" ] && exit 1
set -e

echo "OK"
exit 0
