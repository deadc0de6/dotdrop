#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test empty template generation
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
#echo "dotfile source: ${tmps}"
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"

# globally
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  ignoreempty: true
dotfiles:
  d_d1:
    dst: ${tmpd}/d1
    src: d1
profiles:
  p1:
    dotfiles:
    - d_d1
_EOF
#cat ${cfg}

# create the dotfile
mkdir -p "${tmps}"/dotfiles/d1
echo "{#@@ should be stripped @@#}" > "${tmps}"/dotfiles/d1/empty
echo "not empty" > "${tmps}"/dotfiles/d1/notempty

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

# test existence
[ -e "${tmpd}"/d1/empty ] && echo 'empty should not exist' && exit 1
[ ! -e "${tmpd}"/d1/notempty ] && echo 'not empty should exist' && exit 1

# through the dotfile
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  ignoreempty: false
dotfiles:
  d_d1:
    dst: ${tmpd}/d1
    src: d1
    ignoreempty: true
profiles:
  p1:
    dotfiles:
    - d_d1
_EOF
#cat ${cfg}

# clean destination
rm -rf "${tmpd:?}"/*

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

# test existence
[ -e "${tmpd}"/d1/empty ] && echo 'empty should not exist' && exit 1
[ ! -e "${tmpd}"/d1/notempty ] && echo 'not empty should exist' && exit 1

echo "OK"
exit 0
