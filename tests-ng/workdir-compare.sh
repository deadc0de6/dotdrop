#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2021, deadc0de6
#
# test workdir compare and warn on untracked files
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
unset DOTDROP_WORKDIR

# the dotfile source
tmp=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

tmpf="${tmp}/dotfiles"
tmpw="${tmp}/workdir"
export DOTDROP_WORKDIR="${tmpw}"

mkdir -p "${tmpf}"
echo "dotfiles source (dotpath): ${tmpf}"
mkdir -p "${tmpw}"
echo "workdir: ${tmpw}"

# create the config file
cfg="${tmp}/config.yaml"
echo "config file: ${cfg}"

# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
echo "dotfiles destination: ${tmpd}"

clear_on_exit "${tmp}"
clear_on_exit "${tmpd}"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  workdir: ${tmpw}
  compare_workdir: true
dotfiles:
  f_a:
    dst: ${tmpd}/a
    src: a
    link: link
  f_b:
    dst: ${tmpd}/b
    src: b
    link: nolink
  d_c:
    dst: ${tmpd}/c
    src: c
    link: link_children
profiles:
  p1:
    dotfiles:
    - f_a
    - f_b
    - d_c
_EOF
#cat ${cfg}

# create the dotfile
echo "{{@@ profile @@}}" > "${tmpf}"/a
echo "{{@@ profile @@}}" > "${tmpf}"/b
mkdir -p "${tmpf}"/c
echo "{{@@ profile @@}}" > "${tmpf}"/c/a
echo "{{@@ profile @@}}" > "${tmpf}"/c/b
mkdir "${tmpf}"/c/x
echo "{{@@ profile @@}}" > "${tmpf}"/c/x/a
echo "{{@@ profile @@}}" > "${tmpf}"/c/x/b

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b

# compare (no diff)
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1 -b -V

# add file
touch "${tmpw}"/untrack

# compare (one diff)
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1 -b -V
[ "$?" != "1" ] && echo "not found untracked file in workdir (1)" && exit 1
set -e

# clean
rm "${tmpw}"/untrack
# add sub file
touch "${tmpw}"/"${tmpd}"/c/x/untrack

# compare (two diff)
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1 -b -V
[ "$?" != "1" ] && echo "not found untracked file in workdir (2)" && exit 1
set -e

# clean
rm "${tmpw}"/"${tmpd}"/c/x/untrack
# add dir
mkdir "${tmpw}"/d_untrack
touch "${tmpw}"/d_untrack/untrack

# compare (three diffs)
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1 -b -V
[ "$?" != "1" ] && echo "not found untracked file in workdir (3)" && exit 1
set -e

# clean
rm -r "${tmpw}"/d_untrack
# add sub dir
mkdir "${tmpw}"/"${tmpd}"/c/x/d_untrack
touch "${tmpw}"/"${tmpd}"/c/x/d_untrack/untrack

# compare
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1 -b -V
[ "$?" != "1" ] && echo "not found untracked file in workdir (4)" && exit 1
set -e

## CLEANING
rm -rf "${tmp}" "${tmpd}"

echo "OK"
exit 0
