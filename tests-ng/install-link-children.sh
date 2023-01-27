#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test link_dotfile_default
# returns 1 in case of error
#

# exit on first error
set -e

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
  bin="coverage run -a --source=dotdrop -m dotdrop.dotdrop"
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

# the dotfile source
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_dotfile_default: nolink
dotfiles:
  d_dir1:
    dst: ${tmpd}/dir1
    src: dir1
    link: link_children
    instignore:
      - '*ignore'
profiles:
  p1:
    dotfiles:
    - d_dir1
_EOF
#cat ${cfg}

# create the dotfile
mkdir "${tmps}"/dotfiles/dir1
mkdir "${tmps}"/dotfiles/dir1/empty
echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/dir1/empty/this.ignore
mkdir "${tmps}"/dotfiles/dir1/not-empty
echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/dir1/not-empty/file
mkdir "${tmps}"/dotfiles/dir1/sub
mkdir "${tmps}"/dotfiles/dir1/sub/empty
echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/dir1/sub/empty/that.ignore

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V
#cat ${cfg}

# check normal
[ ! -d "${tmpd}"/dir1 ] && exit 1
[ -d "${tmpd}"/dir1/empty ] && exit 1
[ -d "${tmpd}"/dir1/sub ] && exit 1
[ -d "${tmpd}"/dir1/sub/empty ] && exit 1
[ ! -d "${tmpd}"/dir1/not-empty ] && exit 1

[ ! -e "${tmpd}"/dir1/not-empty/file ] && exit 1

# ignored files
[ -e "${tmpd}"/dir1/empty/this.ignore ] && exit 1
[ -e "${tmpd}"/dir1/sub/empty/that.ignore ] && exit 1

cat "${tmpd}"/dir1/not-empty/file
grep "p1" "${tmpd}"/dir1/not-empty/file

echo "OK"
exit 0
