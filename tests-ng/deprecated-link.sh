#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test migration from link/link_children to single entry
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
[ ! -d ${ddpath} ] && echo "ddpath \"${ddpath}\" is not a directory" && exit 1

export PYTHONPATH="${ddpath}:${PYTHONPATH}"
bin="python3 -m dotdrop.dotdrop"

echo "dotdrop path: ${ddpath}"
echo "pythonpath: ${PYTHONPATH}"

# get the helpers
source ${cur}/helpers

echo -e "$(tput setaf 6)==> RUNNING $(basename $BASH_SOURCE) <==$(tput sgr0)"

################################################################
# this is the test
################################################################

# the dotfile source
tmps=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
mkdir -p ${tmps}/dotfiles
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
config:
  backup: false
  create: true
  dotpath: dotfiles
  link_by_default: true
dotfiles:
  f_link:
    dst: ${tmpd}/abc
    src: abc
    link: true
  f_link1:
    dst: ${tmpd}/abc
    src: abc
    link: true
  f_nolink:
    dst: ${tmpd}/abc
    src: abc
    link: false
  f_nolink1:
    dst: ${tmpd}/abc
    src: abc
    link: false
  f_children:
    dst: ${tmpd}/abc
    src: abc
    link_children: true
  f_children2:
    dst: ${tmpd}/abc
    src: abc
    link_children: true
  f_children3:
    dst: ${tmpd}/abc
    src: abc
    link_children: false
profiles:
  p1:
    dotfiles:
    - f_link
    - f_nolink
    - f_nolink1
    - f_children
    - f_children2
    - f_children3
_EOF
cat ${cfg}

# create the dotfiles
echo "test" > ${tmps}/dotfiles/abc
echo "test" > ${tmpd}/abc

# compare
cd ${ddpath} | ${bin} compare -c ${cfg} -p p1
# install
#cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

cat ${cfg}

# fail if find some of these entries
echo "========> test for bad entries"
set +e
grep 'link_children: true' ${cfg} >/dev/null && exit 1
grep 'link_children: false' ${cfg} >/dev/null && exit 1
grep 'link: true' ${cfg} >/dev/null && exit 1
grep 'link: false' ${cfg} >/dev/null && exit 1
grep 'link_by_default: true' ${cfg} >/dev/null && exit 1
grep 'link_by_default: false' ${cfg} >/dev/null && exit 1
set -e

# test values have been correctly updated
echo "========> test for updated entries"
dotfiles=`cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 | grep -v '^ '`
echo "${dotfiles}" | grep '^f_link ' | grep ', link: link)'
echo "${dotfiles}" | grep '^f_nolink ' | grep ', link: nolink)'
echo "${dotfiles}" | grep '^f_nolink1 ' | grep ', link: nolink)'
echo "${dotfiles}" | grep '^f_children ' | grep ', link: link_children)'
echo "${dotfiles}" | grep '^f_children2 ' | grep ', link: link_children)'
echo "${dotfiles}" | grep '^f_children3 ' | grep ', link: nolink)'

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
