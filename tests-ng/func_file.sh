#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test jinja2 functions from func_file
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
func_file=$(mktemp)
func_file2=$(mktemp)
func_file3=$(mktemp)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${func_file}"
clear_on_exit "${func_file2}"
clear_on_exit "${func_file3}"

# create the config file
cfg="${tmps}/config.yaml"
cfgext="${tmps}/ext.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  func_file:
  - ${func_file}
  - ${func_file2}
  import_configs:
  - ${cfgext}
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
variables:
  func: "{{@@ func1(False) @@}}"
_EOF
#cat ${cfg}

cat > "${cfgext}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  func_file:
  - ${func_file3}
dotfiles:
profiles:
_EOF

cat << _EOF > "${func_file}"
def func1(something):
  if something:
    return True
  return False
_EOF

cat << _EOF > "${func_file2}"
def func2(inp):
  return not inp
_EOF

cat << _EOF > "${func_file3}"
def func3(inp):
  return 42
_EOF

# create the dotfile
echo "this is the test dotfile" > "${tmps}"/dotfiles/abc

# test imported function
echo "{%@@ if func1(True) @@%}" >> "${tmps}"/dotfiles/abc
echo "this should exist" >> "${tmps}"/dotfiles/abc
echo "{%@@ endif @@%}" >> "${tmps}"/dotfiles/abc

echo "{%@@ if not func1(False) @@%}" >> "${tmps}"/dotfiles/abc
echo "this should exist too" >> "${tmps}"/dotfiles/abc
echo "{%@@ endif @@%}" >> "${tmps}"/dotfiles/abc

echo "{%@@ if func2(True) @@%}" >> "${tmps}"/dotfiles/abc
echo "nope" >> "${tmps}"/dotfiles/abc
echo "{%@@ endif @@%}" >> "${tmps}"/dotfiles/abc

echo "{%@@ if func2(False) @@%}" >> "${tmps}"/dotfiles/abc
echo "yes" >> "${tmps}"/dotfiles/abc
echo "{%@@ endif @@%}" >> "${tmps}"/dotfiles/abc

echo "{%@@ if func3(\"whatever\") == 42 @@%}" >> "${tmps}"/dotfiles/abc
echo "externalok" >> "${tmps}"/dotfiles/abc
echo "{%@@ endif @@%}" >> "${tmps}"/dotfiles/abc

echo "{{@@ func @@}}added" >> "${tmps}"/dotfiles/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

#cat ${tmpd}/abc

grep '^this should exist$' "${tmpd}"/abc >/dev/null
grep '^this should exist too$' "${tmpd}"/abc >/dev/null
grep '^yes$' "${tmpd}"/abc >/dev/null
grep '^externalok$' "${tmpd}"/abc >/dev/null
set +e
grep '^nope$' "${tmpd}"/abc >/dev/null && exit 1
set -e
grep '^Falseadded$' "${tmpd}"/abc >/dev/null

echo "OK"
exit 0
