#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test the use of the keyword "include"
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
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p0:
    include:
    - p3
  p1:
    dotfiles:
    - f_abc
  p2:
    include:
    - p1
  p3:
    include:
    - p2
_EOF

# create the source
mkdir -p ${tmps}/dotfiles/
echo "test" > ${tmps}/dotfiles/abc

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1

# compare
cd ${ddpath} | ${bin} compare -c ${cfg} -p p1
cd ${ddpath} | ${bin} compare -c ${cfg} -p p2
cd ${ddpath} | ${bin} compare -c ${cfg} -p p3
cd ${ddpath} | ${bin} compare -c ${cfg} -p p0

# list
cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 | grep f_abc
cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p2 | grep f_abc
cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p3 | grep f_abc
cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p0 | grep f_abc

# count
cnt=`cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -b | grep '^f_' | wc -l`
[ "${cnt}" != "1" ] && exit 1

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
