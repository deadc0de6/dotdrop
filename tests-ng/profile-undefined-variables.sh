#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test variables defined in a different profile
# than the one selected
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
#echo "dotfile destination: ${tmpd}"

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
    dst: "${tmpd}/{{@@ defined_in_main @@}}"
    src: abc
  f_def:
    dst: "${tmpd}/{{@@ defined_in_alt @@}}"
    src: def
profiles:
  pmain:
    dynvariables:
      defined_in_main: echo abc
    dotfiles:
    - f_abc
  palt:
    dynvariables:
      defined_in_alt: echo def
    dotfiles:
    - f_def
  pall:
    dynvariables:
      defined_in_main: echo abcall
      defined_in_alt: echo defall
    dotfiles:
    - ALL
  pinclude:
    include:
    - pmain
_EOF
#cat ${cfg}

# create the dotfile
echo "main" > "${tmps}"/dotfiles/abc
echo "alt" > "${tmps}"/dotfiles/def

# install pmain
echo "install pmain"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p pmain -V
[ ! -e "${tmpd}"/abc ] && echo "dotfile not installed" && exit 1
grep main "${tmpd}"/abc

# install pall
echo "install pall"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p pall -V
[ ! -e "${tmpd}"/abcall ] && echo "dotfile not installed" && exit 1
grep main "${tmpd}"/abcall
[ ! -e "${tmpd}"/defall ] && echo "dotfile not installed" && exit 1
grep alt "${tmpd}"/defall

# install pinclude
echo "install pinclude"
rm -f "${tmpd}"/abc
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p pinclude -V
[ ! -e "${tmpd}"/abc ] && echo "dotfile not installed" && exit 1
grep main "${tmpd}"/abc

echo "OK"
exit 0
