#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# ensure link_children update does not traverse managed symlink trees
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

# create the dotfile and nested hierarchy
mkdir -p "${tmps}"/dotfiles/dir1/child/sub
echo 'nested-content' > "${tmps}"/dotfiles/dir1/child/sub/nested
echo 'root-content' > "${tmps}"/dotfiles/dir1/root-file

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  d_linkchildren:
    src: dir1
    dst: ${tmpd}/dir1
    link: link_children
profiles:
  p1:
    dotfiles:
    - d_linkchildren
_EOF

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

# direct children are symlinked
[ ! -h "${tmpd}"/dir1/child ] && echo "child is not a symlink" && exit 1
[ ! -h "${tmpd}"/dir1/root-file ] && echo "root-file is not a symlink" && exit 1

# update should not walk/traverse managed symlink children
out=$(cd "${ddpath}" | ${bin} update -f -c "${cfg}" -p p1 -V "${tmpd}"/dir1 2>&1)

echo "${out}" | grep "added file to list of ${tmpd}/dir1" && echo "link_children update traversed destination symlink tree" && exit 1
echo "${out}" | grep "added dir to list of ${tmpd}/dir1" && echo "link_children update traversed destination symlink tree" && exit 1

echo "OK"
exit 0
