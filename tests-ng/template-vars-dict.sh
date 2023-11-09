#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6
#
# use of template _vars
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

# dotdrop directory
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
echo "[+] dotdrop dir: ${tmps}"
echo "[+] dotpath dir: ${tmps}/dotfiles"

# dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

cat << _EOF > "${tmps}"/dotfiles/abc
BEGIN
{%@@ for key in _vars @@%}
key:{{@@ key @@}},value:{{@@ _vars[key] @@}}
{%@@ endfor @@%}
END
_EOF

# create the config file
cfg="${tmps}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    src: abc
    dst: ${tmpd}/abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

echo "[+] install"
cd "${ddpath}" | ${bin} install -c "${cfg}" -f -p p1 --verbose
[ "$?" != "0" ] && exit 1

[ ! -f "${tmpd}/abc" ] && echo "abc not installed" && exit 1
cat "${tmpd}/abc"
cat "${tmpd}/abc" | grep 'key:profile,value:p1'
cat "${tmpd}/abc" | grep "key:_dotdrop_cfgpath,value:${tmps}/config.yaml"
cat "${tmpd}/abc" | grep "key:_dotdrop_workdir,value:${DOTDROP_WORKDIR}"
cat "${tmpd}/abc" | grep "key:_dotdrop_dotpath,value:${tmps}/dotfiles"

echo "OK"
exit 0
