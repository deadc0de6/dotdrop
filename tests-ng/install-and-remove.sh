#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6
#
# test install and remove existing file in fs
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

# create the config file
cfg="${basedir}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  d_dir:
    src: dir
    dst: ${tmpd}/dir
profiles:
  p1:
    dotfiles:
    - d_dir
_EOF

# create the file in dotpath
mkdir -p "${basedir}"/dotfiles/dir
echo "content" > "${basedir}"/dotfiles/dir/file

# create the file in fs
mkdir -p "${tmpd}"/dir
echo "content" > "${tmpd}"/dir/existing

echo "[+] install"
cd "${ddpath}" | ${bin} install -c "${cfg}" -f -p p1 --verbose
[ "$?" != "0" ] && exit 1

[ ! -e "${tmpd}"/dir/file ] && echo "d_dir file not installed" && exit 1
[ ! -e "${tmpd}"/dir/existing ] && echo "existing removed" && exit 1

echo "[+] install with remove"
cd "${ddpath}" | ${bin} install --remove-existing -c "${cfg}" -f -p p1 --verbose
[ "$?" != "0" ] && exit 1

[ ! -e "${tmpd}"/dir/file ] && echo "d_dir file not installed" && exit 1
[ -e "${tmpd}"/dir/existing ] && echo "existing not removed" && exit 1

echo "OK"
exit 0
