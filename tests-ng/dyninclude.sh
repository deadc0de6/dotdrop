#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test dynamic includes
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
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
variables:
  var1: "_1"
dynvariables:
  dvar1: "echo _2"
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
profiles:
  profile_1:
    dotfiles:
    - f_abc
  profile_2:
    dotfiles:
    - f_def
  profile_3:
    include:
    - profile{{@@ var1 @@}}
  profile_4:
    include:
    - profile{{@@ dvar1 @@}}
_EOF
#cat ${cfg}

# create the dotfile
c1="content:abc"
echo "${c1}" > "${tmps}"/dotfiles/abc
c2="content:def"
echo "${c2}" > "${tmps}"/dotfiles/def

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p profile_3 --verbose

# check dotfile exists
[ ! -e "${tmpd}"/abc ] && exit 1
#cat ${tmpd}/abc
grep ${c1} "${tmpd}"/abc >/dev/null || exit 1

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p profile_4 --verbose

# check dotfile exists
[ ! -e "${tmpd}"/def ] && exit 1
#cat ${tmpd}/def
grep ${c2} "${tmpd}"/def >/dev/null || exit 1

echo "OK"
exit 0
