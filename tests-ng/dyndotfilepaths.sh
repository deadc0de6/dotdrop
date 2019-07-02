#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test dynamic variables in dotfile src/dst
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

dst=`echo ${tmpd} | rev`

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dynvariables:
  dpath: echo ${dst} | rev
dotfiles:
  f_abc:
    dst: "{{@@ dpath @@}}/abc"
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo "{{@@ dpath @@}}" > ${tmps}/dotfiles/abc

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

#cat ${tmpd}/abc

[ ! -e ${tmpd}/abc ] && echo "abc not installed dynamically" && exit 1
grep "^${tmpd}" ${tmpd}/abc >/dev/null

#cat ${tmpd}/abc

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
