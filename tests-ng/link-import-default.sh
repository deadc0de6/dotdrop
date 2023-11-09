#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test the use of the keyword "link_on_import"
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

# create the source
echo "abc" > "${tmpd}"/abc

# import with nolink by default
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_on_import: nolink
dotfiles:
profiles:
_EOF

# import
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V "${tmpd}"/abc

# checks
inside="${tmps}/dotfiles/${tmpd}/abc"
[ ! -e "${inside}" ] && exit 1

set +e
cat "${cfg}" | grep 'link:' && exit 1
set -e

# import with parent by default
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_on_import: link
dotfiles:
profiles:
_EOF

# import
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V "${tmpd}"/abc

# checks
inside="${tmps}/dotfiles/${tmpd}/abc"
[ ! -e "${inside}" ] && exit 1

cat "${cfg}"
cat "${cfg}" | grep 'link: absolute' >/dev/null

echo "OK"
exit 0
