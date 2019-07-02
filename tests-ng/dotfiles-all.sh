#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test ALL dotfiles
# returns 1 in case of error
#

# exit on first error
set -e
#set -v

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
echo "dotfiles source (dotpath): ${tmps}"
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
echo "dotfiles destination: ${tmpd}"

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
  f_def:
    dst: ${tmpd}/def
    src: def
  d_ghi:
    dst: ${tmpd}/ghi
    src: ghi
profiles:
  p1:
    dotfiles:
    - ALL
_EOF
#cat ${cfg}

# create the dotfiles
echo "abc" > ${tmps}/dotfiles/abc
echo "def" > ${tmps}/dotfiles/def
echo "ghi" > ${tmps}/dotfiles/ghi

###########################
# test install and compare
###########################

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -b -V
[ "$?" != "0" ] && exit 1

# checks
[ ! -e ${tmpd}/abc ] && exit 1
[ ! -e ${tmpd}/def ] && exit 1
[ ! -e ${tmpd}/ghi ] && exit 1

# modify the dotfiles
echo "abc-modified" > ${tmps}/dotfiles/abc
echo "def-modified" > ${tmps}/dotfiles/def
echo "ghi-modified" > ${tmps}/dotfiles/ghi

# compare
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} -p p1 -b -V
ret="$?"
set -e
[ "$ret" = "0" ] && exit 1

## CLEANING
rm -rf ${tmps} ${tmpd} ${tmpx} ${tmpy}

echo "OK"
exit 0
