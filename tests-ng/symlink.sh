#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test symlinking dotfiles
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

##################################################
# test symlink directory
##################################################
# create the dotfile
mkdir -p "${tmps}"/dotfiles/abc
echo "file1" > "${tmps}"/dotfiles/abc/file1
echo "file2" > "${tmps}"/dotfiles/abc/file2

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
    link: link
profiles:
  p1:
    dotfiles:
    - d_abc
_EOF
#cat ${cfg}

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V
#cat ${cfg}

# ensure exists and is link
[ ! -h "${tmpd}"/abc ] && echo "not a symlink" && exit 1
[ ! -e "${tmpd}"/abc/file1 ] && echo "does not exist" && exit 1
[ ! -e "${tmpd}"/abc/file2 ] && echo "does not exist" && exit 1

##################################################
# test symlink files
##################################################
# clean
rm -rf "${tmps}"/dotfiles "${tmpd}"/abc

# create the dotfiles
mkdir -p "${tmps}"/dotfiles/
echo "abc" > "${tmps}"/dotfiles/abc

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
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    link: link
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V
#cat ${cfg}

# ensure exists and is link
[ ! -h "${tmpd}"/abc ] && echo "not a symlink" && exit 1

##################################################
# test link_children
##################################################
# clean
rm -rf "${tmps}"/dotfiles "${tmpd}"/abc

# create the dotfile
mkdir -p "${tmps}"/dotfiles/abc
echo "file1" > "${tmps}"/dotfiles/abc/file1
echo "file2" > "${tmps}"/dotfiles/abc/file2

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
    link: link_children
profiles:
  p1:
    dotfiles:
    - d_abc
_EOF
#cat ${cfg}

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V
#cat ${cfg}

# ensure exists and is link
[ ! -d "${tmpd}"/abc ] && echo "not a symlink" && exit 1
[ ! -h "${tmpd}"/abc/file1 ] && echo "does not exist" && exit 1
[ ! -h "${tmpd}"/abc/file2 ] && echo "does not exist" && exit 1

##################################################
# test link_children with templates
##################################################
# clean
rm -rf "${tmps}"/dotfiles "${tmpd}"/abc

# create the dotfile
mkdir -p "${tmps}"/dotfiles/abc
echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/abc/file1
echo "file2" > "${tmps}"/dotfiles/abc/file2

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
    link: link_children
profiles:
  p1:
    dotfiles:
    - d_abc
_EOF
#cat ${cfg}

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V
#cat ${cfg}

# ensure exists and is link
[ ! -d "${tmpd}"/abc ] && echo "not a symlink" && exit 1
[ ! -h "${tmpd}"/abc/file1 ] && echo "does not exist" && exit 1
[ ! -h "${tmpd}"/abc/file2 ] && echo "does not exist" && exit 1
grep '^p1$' "${tmpd}"/abc/file1

echo "OK"
exit 0
