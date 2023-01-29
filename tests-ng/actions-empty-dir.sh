#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test pre/post/naked actions
# returns 1 in case of error
#

# exit on first error
set -ev

# all this crap to get current path
rl="readlink -f"
if ! ${rl} "${0}" >/dev/null 2>&1; then
  rl="realpath"

  if ! hash ${rl}; then
    echo "\"${rl}\" not found !" && exit 1
  fi
fi
cur=$(dirname "$(${rl} "${0}")")

#hash dotdrop >/dev/null 2>&1
#[ "$?" != "0" ] && echo "install dotdrop to run tests" && exit 1

#echo "called with ${1}"

# dotdrop path can be pass as argument
ddpath="${cur}/../"
[ "${1}" != "" ] && ddpath="${1}"
[ ! -d "${ddpath}" ] && echo "ddpath \"${ddpath}\" is not a directory" && exit 1

export PYTHONPATH="${ddpath}:${PYTHONPATH}"
bin="python3 -m dotdrop.dotdrop"
if hash coverage 2>/dev/null; then
  bin="coverage run -p --source=dotdrop -m dotdrop.dotdrop"
fi

echo "dotdrop path: ${ddpath}"
echo "pythonpath: ${PYTHONPATH}"

# get the helpers
# shellcheck source=tests-ng/helpers
source "${cur}"/helpers

echo -e "$(tput setaf 6)==> RUNNING $(basename "${BASH_SOURCE[0]}") <==$(tput sgr0)"

################################################################
# this is the test
################################################################

# the action temp
tmpa=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
# the dotfile source
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpa}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
actions:
  clearemptydir: find -L '{0}' -empty -xtype d -delete
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_dir1:
    dst: ${tmpd}/dir1
    src: dir1
    ignoreempty: true
    actions:
      - clearemptydir ${tmpd}/dir1
    instignore:
      - '*ignore'
  f_dir2:
    dst: ${tmpd}/dir2
    src: dir2
    link: link_children
    ignoreempty: true
    actions:
      - clearemptydir ${tmpd}/dir2
    instignore:
      - '*ignore'
  f_dir3:
    dst: ${tmpd}/dir3
    src: dir3
    link: link
    ignoreempty: true
    actions:
      - clearemptydir ${tmpd}/dir3
    instignore:
      - '*ignore'
profiles:
  p1:
    dotfiles:
    - f_dir1
    - f_dir2
    - f_dir3
_EOF
#cat ${cfg}

# create the dotfile
mkdir "${tmps}"/dotfiles/dir1
mkdir "${tmps}"/dotfiles/dir1/empty
echo "to-ignore" > "${tmps}"/dotfiles/dir1/empty/this.ignore
mkdir "${tmps}"/dotfiles/dir1/not-empty
echo "file" > "${tmps}"/dotfiles/dir1/not-empty/file
mkdir "${tmps}"/dotfiles/dir1/sub
mkdir "${tmps}"/dotfiles/dir1/sub/empty
echo "to-ignore-too" > "${tmps}"/dotfiles/dir1/sub/empty/that.ignore

# create the dotfile
mkdir "${tmps}"/dotfiles/dir2
mkdir "${tmps}"/dotfiles/dir2/empty
echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/dir2/empty/this.ignore
mkdir "${tmps}"/dotfiles/dir2/not-empty
echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/dir2/not-empty/file
mkdir "${tmps}"/dotfiles/dir2/sub
mkdir "${tmps}"/dotfiles/dir2/sub/empty
echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/dir2/sub/empty/that.ignore

# create the dotfile
mkdir "${tmps}"/dotfiles/dir3
mkdir "${tmps}"/dotfiles/dir3/empty
echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/dir3/empty/this.ignore
mkdir "${tmps}"/dotfiles/dir3/not-empty
echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/dir3/not-empty/file
mkdir "${tmps}"/dotfiles/dir3/sub
mkdir "${tmps}"/dotfiles/dir3/sub/empty
echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/dir3/sub/empty/that.ignore

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

# checks normal
[ ! -d "${tmpd}"/dir1 ] && exit 1
[ -d "${tmpd}"/dir1/empty ] && exit 1
[ -e "${tmpd}"/dir1/empty/this.ignore ] && exit 1
[ ! -d "${tmpd}"/dir1/not-empty ] && exit 1
[ ! -e "${tmpd}"/dir1/not-empty/file ] && exit 1
[ -d "${tmpd}"/dir1/sub ] && exit 1
[ -d "${tmpd}"/dir1/sub/empty ] && exit 1
[ -e "${tmpd}"/dir1/sub/empty/that.ignore ] && exit 1
grep "file" "${tmpd}"/dir1/not-empty/file

# checks link_children
[ ! -d "${tmpd}"/dir2 ] && exit 1
[ ! -h "${tmpd}"/dir2/empty ] && exit 1
[ -e "${tmpd}"/dir2/empty/this.ignore ] && exit 1
[ ! -d "${tmpd}"/dir2/not-empty ] && exit 1
[ ! -h "${tmpd}"/dir2/not-empty ] && exit 1
[ ! -e "${tmpd}"/dir2/not-empty/file ] && exit 1
[ -d "${tmpd}"/dir2/sub ] && exit 1
[ -d "${tmpd}"/dir2/sub/empty ] && exit 1
[ -e "${tmpd}"/dir2/sub/empty/that.ignore ] && exit 1
grep "p1" "${tmpd}"/dir2/not-empty/file

# checks link
[ ! -d "${tmpd}"/dir3 ] && exit 1
[ ! -h "${tmpd}"/dir3 ] && exit 1
[ -d "${tmpd}"/dir3/empty ] && exit 1
[ -e "${tmpd}"/dir3/empty/this.ignore ] && exit 1
[ ! -d "${tmpd}"/dir3/not-empty ] && exit 1
[ ! -e "${tmpd}"/dir3/not-empty/file ] && exit 1
[ -d "${tmpd}"/dir3/sub ] && exit 1
[ -d "${tmpd}"/dir3/sub/empty ] && exit 1
[ -e "${tmpd}"/dir3/sub/empty/that.ignore ] && exit 1
grep "p1" "${tmpd}"/dir3/not-empty/file

# second install won't trigger the action
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V  # 2>&1 | tee ${tmpa}/log

# check normal
[ -d "${tmpd}"/dir1/empty ] && echo "empty directory not cleaned" && exit 1
[ -d "${tmpd}"/dir1/sub/empty ] && echo "empty directory not cleaned" && exit 1

# check link_children
[ -d "${tmpd}"/dir2/empty ] && echo "empty directory not cleaned" && exit 1
[ -d "${tmpd}"/dir2/sub/empty ] && echo "empty directory not cleaned" && exit 1

# check link
[ -d "${tmpd}"/dir3/empty ] && echo "empty directory not cleaned" && exit 1
[ -d "${tmpd}"/dir3/sub/empty ] && echo "empty directory not cleaned" && exit 1

echo "OK"
exit 0
