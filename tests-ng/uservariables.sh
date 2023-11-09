#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2021, deadc0de6
#
# test user variables from yaml file
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
  import_variables:
    - uservariables.yaml:optional
variables:
  var4: "variables_var4"
dynvariables:
  var3: "echo dynvariables_var3"
uservariables:
  var1: "var1"
  var2: "var2"
  var3: "var3"
  var4: "var4"
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo "var1: {{@@ var1 @@}}" > "${tmps}"/dotfiles/abc
echo "var2: {{@@ var2 @@}}" >> "${tmps}"/dotfiles/abc
echo "var3: {{@@ var3 @@}}" >> "${tmps}"/dotfiles/abc
echo "var4: {{@@ var4 @@}}" >> "${tmps}"/dotfiles/abc

# install
echo "step 1"
(
  cd "${ddpath}"
  printf 'var1contentxxx\nvar2contentyyy\nvar3\nvar4\n' | ${bin} install -f -c "${cfg}" -p p1 -V
  exit ${?}
)

cat "${tmpd}"/abc

grep '^var1: var1contentxxx$' "${tmpd}"/abc >/dev/null
grep '^var2: var2contentyyy$' "${tmpd}"/abc >/dev/null
grep '^var3: dynvariables_var3$' "${tmpd}"/abc >/dev/null
grep '^var4: variables_var4$' "${tmpd}"/abc >/dev/null

[ ! -e "${tmps}/uservariables.yaml" ] && exit 1

grep '^variables:' "${tmps}"/uservariables.yaml >/dev/null
grep '^  var1: var1contentxxx$' "${tmps}"/uservariables.yaml >/dev/null
grep '^  var2: var2contentyyy$' "${tmps}"/uservariables.yaml >/dev/null

cat > "${tmps}/uservariables.yaml" << _EOF
variables:
  var1: editedvar1
  var2: editedvar2
_EOF

echo "step 2"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

grep '^var1: editedvar1$' "${tmpd}"/abc >/dev/null
grep '^var2: editedvar2$' "${tmpd}"/abc >/dev/null
grep '^var3: dynvariables_var3$' "${tmpd}"/abc >/dev/null
grep '^var4: variables_var4$' "${tmpd}"/abc >/dev/null

echo "OK"
exit 0
