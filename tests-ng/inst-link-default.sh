#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test link_dotfile_default
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

# create the dotfile
mkdir -p "${tmps}"/dotfiles/abc
echo "test link_dotfile_default 1" > "${tmps}"/dotfiles/abc/file1
echo "test link_dotfile_default 2" > "${tmps}"/dotfiles/abc/file2
echo "should be linked" > "${tmps}"/dotfiles/def

# create a shell script
# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_dotfile_default: nolink
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

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V
#cat ${cfg}

# ensure exists and is not link
[ ! -d "${tmpd}"/abc ] && echo "not a directory" && exit 1
[ -h "${tmpd}"/abc ] && echo "not a regular file" && exit 1
[ ! -e "${tmpd}"/abc/file1 ] && echo "not exist" && exit 1
[ -h "${tmpd}"/abc/file1 ] && echo "not a regular file" && exit 1
[ ! -e "${tmpd}"/abc/file2 ] && echo "not exist" && exit 1
[ -h "${tmpd}"/abc/file2 ] && echo "not a regular file" && exit 1
rm -rf "${tmpd}"/abc

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_dotfile_default: link
dotfiles:
  d_abc:
    dst: ${tmpd}/abc
    src: abc
  f_def:
    dst: ${tmpd}/def
    src: def
profiles:
  p1:
    dotfiles:
    - d_abc
    - f_def
_EOF

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V
#cat ${cfg}

# ensure exists and parent is a link
[ ! -e "${tmpd}"/abc ] && echo "not exist" && exit 1
[ ! -h "${tmpd}"/abc ] && echo "not a symlink" && exit 1
[ ! -e "${tmpd}"/abc/file1 ] && echo "not exist" && exit 1
[ -h "${tmpd}"/abc/file1 ] && echo "not a regular file" && exit 1
[ ! -e "${tmpd}"/abc/file2 ] && echo "not exist" && exit 1
[ -h "${tmpd}"/abc/file2 ] && echo "not a regular file" && exit 1
rm -rf "${tmpd}"/abc

[ ! -e "${tmpd}"/def ] && echo "not exist" && exit 1
[ ! -h "${tmpd}"/def ] && echo "not a symlink" && exit 1
rm -f "${tmpd}"/def

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_dotfile_default: link_children
dotfiles:
  d_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - d_abc
_EOF

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V
#cat ${cfg}

# ensure exists and children are links
[ ! -e "${tmpd}"/abc ] && echo "not exist" && exit 1
[ -h "${tmpd}"/abc ] && echo "not a regular file" && exit 1
[ ! -e "${tmpd}"/abc/file1 ] && echo "not exist" && exit 1
[ ! -h "${tmpd}"/abc/file1 ] && echo "not a symlink" && exit 1
[ ! -e "${tmpd}"/abc/file2 ] && echo "not exist" && exit 1
[ ! -h "${tmpd}"/abc/file2 ] && echo "not a symlink" && exit 1
rm -rf "${tmpd}"/abc

echo "OK"
exit 0
