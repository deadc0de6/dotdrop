#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test dotfile sub file specific variables
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

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  d_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - d_abc
_EOF
#cat ${cfg}

# create the dotfile
mkdir -p "${tmps}"/dotfiles/abc
# file1
echo 'src:{{@@ _dotfile_sub_abs_src @@}}' > "${tmps}"/dotfiles/abc/file1
echo 'dst:{{@@ _dotfile_sub_abs_dst @@}}' >> "${tmps}"/dotfiles/abc/file1

# file2
mkdir -p "${tmps}"/dotfiles/abc/subdir
echo 'src:{{@@ _dotfile_sub_abs_src @@}}' > "${tmps}"/dotfiles/abc/subdir/file2
echo 'dst:{{@@ _dotfile_sub_abs_dst @@}}' >> "${tmps}"/dotfiles/abc/subdir/file2

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

# checks
[ ! -d "${tmpd}"/abc ] && echo 'dotfile not installed' && exit 1
[ ! -e "${tmpd}"/abc/file1 ] && echo 'dotfile sub src not installed' && exit 1
[ ! -e "${tmpd}"/abc/subdir/file2 ] && echo 'dotfile sub dst not installed' && exit 1

cat "${tmpd}"/abc/file1
cat "${tmpd}"/abc/subdir/file2

grep "src:${tmps}/dotfiles/abc/file1" "${tmpd}"/abc/file1 >/dev/null
grep "dst:${tmpd}/abc/file1" "${tmpd}"/abc/file1>/dev/null

grep "src:${tmps}/dotfiles/abc/subdir/file2" "${tmpd}"/abc/subdir/file2 >/dev/null
grep "dst:${tmpd}/abc/subdir/file2" "${tmpd}"/abc/subdir/file2 >/dev/null

echo "OK"
exit 0
