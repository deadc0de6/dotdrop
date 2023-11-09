#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# import variables from file
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
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p0:
    dotfiles:
    - f_abc
variables:
  global: global_var
  local: local_var
_EOF

# create the source
mkdir -p "${tmps}"/dotfiles/

cat > "${tmps}"/dotfiles/macro_file << _EOF
{%@@ macro macro(var) @@%}
{{@@ global @@}}
{{@@ var @@}}
{%@@ endmacro @@%}
_EOF

cat > "${tmps}"/dotfiles/abc << _EOF
{%@@ from 'macro_file' import macro with context @@%}
{{@@ macro(local) @@}}
_EOF

# install
cd "${ddpath}" | ${bin} install -c "${cfg}" -p p0 -V -f

# test file content
cat "${tmpd}"/abc
grep 'global_var' "${tmpd}"/abc >/dev/null 2>&1
grep 'local_var' "${tmpd}"/abc >/dev/null 2>&1

echo "OK"
exit 0
