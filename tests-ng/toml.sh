#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6
#
# test toml config
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
tmp=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
tmpf="${tmp}/dotfiles"
mkdir -p "${tmpf}"
echo "dotfiles source (dotpath): ${tmpf}"

# create the config file
cfg="${tmp}/config.toml"
echo "config file: ${cfg}"

# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
echo "dotfiles destination: ${tmpd}"

clear_on_exit "${tmp}"
clear_on_exit "${tmpd}"

## RELATIVE
cat > "${cfg}" << _EOF
[config]
backup = true
create = true
dotpath = "dotfiles"

[dotfiles.f_abc]
dst = "${tmpd}/abc"
src = "abc"
link = true

[profiles.p1]
dotfiles = [ "f_abc",]
_EOF
#cat ${cfg}

# create the dotfile
echo "{{@@ profile @@}}" > "${tmpf}"/abc
echo "{{@@ profile @@}}" > "${tmpd}"/def

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b -V
[ ! -e "${tmpd}"/abc ] && echo "[ERROR] dotfile not installed" && exit 1

# import
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -b -V "${tmpd}"/def
[ ! -e "${tmpf}""${tmpd}"/def ] && echo "[ERROR] dotfile not imported" && exit 1

# checks
cnt=$(cd "${ddpath}" | ${bin} files -G -c "${cfg}" -p p1 -V | grep '^f_' | wc -l)
[ "${cnt}" != "2" ] && echo "[ERROR]" && exit 1

## CLEANING
rm -rf "${tmp}" "${tmpd}"

echo "OK"
exit 0
