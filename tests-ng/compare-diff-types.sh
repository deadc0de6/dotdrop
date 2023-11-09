#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6
#
# test updates
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
mkdir -p "${basedir}/dotfiles"

# the dotfile to be imported
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
  f_file:
    src: file
    dst: ${tmpd}/file
  d_file:
    src: dir
    dst: ${tmpd}/dir
profiles:
  p1:
    dotfiles:
    - f_file
  p2:
    dotfiles:
    - d_file
_EOF

# file and dir
echo "test" > "${basedir}"/dotfiles/file
mkdir "${tmpd}"/file

# dir and file
mkdir "${basedir}"/dotfiles/dir
echo "test" > "${tmpd}"/dir

# compare
echo "[+] comparing p1"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1 --verbose
[ "$?" = "0" ] && exit 1
set -e

echo "[+] comparing p2"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p2 --verbose
[ "$?" = "0" ] && exit 1
set -e

echo "OK"
exit 0
