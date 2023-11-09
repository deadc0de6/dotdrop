#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test missing files ignored as expected
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
tmps=$(mktemp -d --suffix='-dotdrop-tests-source' || mktemp -d)
dt="${tmps}/dotfiles"
mkdir -p "${dt}"/folder
touch "${dt}"/folder/a

# fs dotfiles
tmpd=$(mktemp -d --suffix='-dotdrop-tests-dest' || mktemp -d)
cp -r "${dt}"/folder "${tmpd}"/
touch "${tmpd}"/folder/b
mkdir "${tmpd}"/folder/c
touch "${tmpd}"/folder/c/cfile

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"
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
#cat ${cfg}

#tree ${dt}

#
# Test with no ignore-missing setting
#

# file b / folder c SHOULD be copied
echo "[+] test with no ignore-missing setting"
cd "${ddpath}" | ${bin} update -f -c "${cfg}" --verbose --profile=p1 --key thedotfile

[ ! -e "${dt}"/folder/b ] && echo "${dt}/folder/b should have been updated" && exit 1
[ ! -e "${dt}"/folder/c/cfile ] && echo "${dt}/folder/c/cfile should have been updated" && exit 1

# Reset
rm "${dt}"/folder/b
rm -rf "${dt}"/folder/c

#
# Test with command-line flag
#

# file b / folder c should NOT be copied
echo "[+] test with command-line flag"
cd "${ddpath}" | ${bin} update -f -c "${cfg}" --verbose --profile=p1 --key thedotfile --ignore-missing

[ -e "${dt}"/folder/b ] && echo "should not have been updated" && exit 1
[ -e "${dt}"/folder/c ] && echo "should not have been updated" && exit 1

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

# file b / folder c should NOT be copied
echo "[+] test global option"
cd "${ddpath}" | ${bin} update -f -c "${cfg}" --verbose --profile=p1 --key thedotfile

[ -e "${dt}"/folder/b ] && echo "should not have been updated" && exit 1
[ -e "${dt}"/folder/c ] && echo "should not have been updated" && exit 1

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
# file b / folder c should NOT be copied
echo "[+] test dotfile option"
cd "${ddpath}" | ${bin} update -f -c "${cfg}" --verbose --profile=p1 --key thedotfile

[ -e "${dt}"/folder/b ] && echo "should not have been updated" && exit 1
[ -e "${dt}"/folder/c ] && echo "should not have been updated" && exit 1

echo "OK"
exit 0
