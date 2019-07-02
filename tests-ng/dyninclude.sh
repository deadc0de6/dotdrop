#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test dynamic includes
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
variables:
  var1: "_1"
dynvariables:
  dvar1: "echo _2"
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
  f_def:
    dst: ${tmpd}/def
    src: def
profiles:
  profile_1:
    dotfiles:
    - f_abc
  profile_2:
    dotfiles:
    - f_def
  profile_3:
    include:
    - profile{{@@ var1 @@}}
  profile_4:
    include:
    - profile{{@@ dvar1 @@}}
_EOF
#cat ${cfg}

# create the dotfile
c1="content:abc"
echo "${c1}" > ${tmps}/dotfiles/abc
c2="content:def"
echo "${c2}" > ${tmps}/dotfiles/def

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p profile_3 --verbose

# check dotfile exists
[ ! -e ${tmpd}/abc ] && exit 1
#cat ${tmpd}/abc
grep ${c1} ${tmpd}/abc >/dev/null || exit 1

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p profile_4 --verbose

# check dotfile exists
[ ! -e ${tmpd}/def ] && exit 1
#cat ${tmpd}/def
grep ${c2} ${tmpd}/def >/dev/null || exit 1

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
