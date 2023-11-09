#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6
#
# test dotpath templated
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
