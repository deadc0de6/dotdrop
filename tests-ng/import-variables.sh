#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6
#
# test import_variables
# returns 1 in case of error
# see issue 380
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
cfgvar1="${tmps}/var1.yaml"
cfgvar2="${tmps}/var2.yaml"

cat << _EOF > "${tmps}/dotfiles/abc"
var1: {{@@ var1 @@}}
var2: {{@@ var2 @@}}
var3: {{@@ var3 @@}}
var4: {{@@ var4 @@}}
var5: {{@@ var5 @@}}
var6: {{@@ var6 @@}}
_EOF

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_variables:
  - ${cfgvar1}
  - ${cfgvar2}
variables:
  var1: "this is var1 from main config"
  var2: "this is var2 from main config"
  var3: "this is var3 from main config"
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: 'abc'
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
echo "main config: ${cfg}"
cat "${cfg}"

cat << _EOF > "${cfgvar1}"
variables:
  var2: "this is var2 from sub1"
  var3: "this is var3 from sub1"
  var4: "this is var4 from sub1"
  var5: "this is var5 from sub1"
_EOF
echo "cfgvar1: ${cfgvar1}"
cat "${cfgvar1}"

cat << _EOF > "${cfgvar2}"
variables:
  var3: "this is var3 from sub2"
  var4: "this is var4 from sub2"
  var6: "this is var6 from sub2"
_EOF
echo "cfgvar2: ${cfgvar2}"
cat "${cfgvar2}"

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 --verbose

# test file existence
[ -f "${tmpd}/abc" ] || {
    echo 'Dotfile not installed'
    exit 1
}

# test file content
cat "${tmpd}"/abc
echo "----------------------"
grep '^var1: this is var1 from main config$' "${tmpd}"/abc >/dev/null
echo "var1 ok"
grep '^var2: this is var2 from sub1$' "${tmpd}"/abc >/dev/null
echo "var2 ok"
grep '^var3: this is var3 from sub2$' "${tmpd}"/abc >/dev/null
echo "var3 ok"
grep '^var4: this is var4 from sub2$' "${tmpd}"/abc >/dev/null
echo "var4 ok"
grep '^var5: this is var5 from sub1$' "${tmpd}"/abc >/dev/null
echo "var5 ok"
grep '^var6: this is var6 from sub2$' "${tmpd}"/abc >/dev/null
echo "var6 ok"

echo "OK"
exit 0
