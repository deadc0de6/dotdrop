#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test variables from yaml file
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

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
variables:
  var1: "this is some test"
  var2: 12
  var3: another test
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
    variables:
      var1: "this is some sub-test"
  p2:
    include:
    - p1
    variables:
      var2: 42
_EOF
#cat ${cfg}

# create the dotfile
echo "{{@@ var1 @@}}" > "${tmps}"/dotfiles/abc
echo "{{@@ var2 @@}}" >> "${tmps}"/dotfiles/abc
echo "{{@@ var3 @@}}" >> "${tmps}"/dotfiles/abc
echo "test" >> "${tmps}"/dotfiles/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1

cat "${tmpd}"/abc
grep '^this is some sub-test' "${tmpd}"/abc >/dev/null
grep '^12' "${tmpd}"/abc >/dev/null
grep '^another test' "${tmpd}"/abc >/dev/null

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p2

cat "${tmpd}"/abc
grep '^this is some sub-test' "${tmpd}"/abc >/dev/null
grep '^42' "${tmpd}"/abc >/dev/null
grep '^another test' "${tmpd}"/abc >/dev/null

#cat ${tmpd}/abc

echo "OK"
exit 0
