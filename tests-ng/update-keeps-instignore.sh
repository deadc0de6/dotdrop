#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2026, deadc0de6
#
# test update keeps the files install ignores in the dotpath
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
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
dt="${tmps}/dotfiles"
mkdir -p "${dt}"/testdir
echo 'common' > "${dt}"/testdir/common
echo 'one' > "${dt}"/testdir/ignore-me-1
echo 'two' > "${dt}"/testdir/ignore-me-2

# fs dotfiles
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# the per-profile instignore example from the docs
cfg="${tmps}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: false
  create: true
  dotpath: dotfiles
dotfiles:
  d_testdir_p1:
    src: testdir
    dst: ${tmpd}/testdir
    instignore:
    - '*/ignore-me-1'
  d_testdir_p2:
    src: testdir
    dst: ${tmpd}/testdir
    instignore:
    - '*/ignore-me-2'
profiles:
  p1:
    dotfiles:
    - d_testdir_p1
  p2:
    dotfiles:
    - d_testdir_p2
_EOF

echo "[+] install"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" --verbose --profile=p1
[ -e "${tmpd}"/testdir/ignore-me-1 ] && echo "ignore-me-1 installed" && exit 1

echo "[+] edit and update"
echo 'edited' >> "${tmpd}"/testdir/common
cd "${ddpath}" | ${bin} update -f -c "${cfg}" --verbose --profile=p1

grep -q 'edited' "${dt}"/testdir/common || (echo "common not updated" && exit 1)
[ ! -e "${dt}"/testdir/ignore-me-1 ] && echo "ignore-me-1 removed from dotpath" && exit 1

echo "OK"
exit 0
