#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test ALL dotfiles
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

# the dotfile source
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
echo "dotfiles source (dotpath): ${tmps}"
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
echo "dotfiles destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
  f_def:
    dst: ${tmpd}/def
    src: def
  d_ghi:
    dst: ${tmpd}/ghi
    src: ghi
profiles:
  p1:
    dotfiles:
    - ALL
_EOF
#cat ${cfg}

# create the dotfiles
echo "abc" > "${tmps}"/dotfiles/abc
echo "def" > "${tmps}"/dotfiles/def
echo "ghi" > "${tmps}"/dotfiles/ghi

###########################
# test install and compare
###########################

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b -V
[ "$?" != "0" ] && exit 1

# checks
[ ! -e "${tmpd}"/abc ] && exit 1
[ ! -e "${tmpd}"/def ] && exit 1
[ ! -e "${tmpd}"/ghi ] && exit 1

# modify the dotfiles
echo "abc-modified" > "${tmps}"/dotfiles/abc
echo "def-modified" > "${tmps}"/dotfiles/def
echo "ghi-modified" > "${tmps}"/dotfiles/ghi

# compare
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1 -b -V
ret="$?"
set -e
[ "$ret" = "0" ] && exit 1

echo "OK"
exit 0
