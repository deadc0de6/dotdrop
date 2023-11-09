#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test external config's variables
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
extcfg="${tmps}/ext-config.yaml"
cfg="${tmps}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_configs:
  - $(basename "${extcfg}")
variables:
  varx: "test"
  provar: "local"
dynvariables:
  dvarx: "echo dtest"
  dprovar: "echo dlocal"
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
    variables:
      varx: profvarx
      provar: provar
    dynvariables:
      dvarx: echo dprofvarx
      dprovar: echo dprovar
_EOF
cat "${cfg}"

# create the external variables file
cat > "${extcfg}" << _EOF
config:
profiles:
  p2:
    dotfiles:
    - f_abc
    variables:
      varx: extprofvarx
      provar: extprovar
    dynvariables:
      dvarx: echo extdprofvarx
      dprovar: echo extdprovar
dotfiles:
_EOF
ls -l "${extcfg}"
cat "${extcfg}"

# create the dotfile
echo "varx: {{@@ varx @@}}" > "${tmps}"/dotfiles/abc
echo "provar: {{@@ provar @@}}" >> "${tmps}"/dotfiles/abc
echo "dvarx: {{@@ dvarx @@}}" >> "${tmps}"/dotfiles/abc
echo "dprovar: {{@@ dprovar@@}}" >> "${tmps}"/dotfiles/abc

#cat ${tmps}/dotfiles/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p2 -V

echo "test1"
cat "${tmpd}"/abc
grep '^varx: extprofvarx' "${tmpd}"/abc >/dev/null
grep '^provar: extprovar' "${tmpd}"/abc >/dev/null
grep '^dvarx: extdprofvarx' "${tmpd}"/abc >/dev/null
grep '^dprovar: extdprovar' "${tmpd}"/abc >/dev/null

rm -f "${tmpd}"/abc
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

echo "test2"
cat "${tmpd}"/abc
grep '^varx: profvarx' "${tmpd}"/abc >/dev/null
grep '^provar: provar' "${tmpd}"/abc >/dev/null
grep '^dvarx: dprofvarx' "${tmpd}"/abc >/dev/null
grep '^dprovar: dprovar' "${tmpd}"/abc >/dev/null

echo "OK"
exit 0
