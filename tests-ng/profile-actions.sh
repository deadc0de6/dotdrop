#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test actions per profile
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
#echo "dotfile destination: ${tmpd}"
# the action temp
tmpa=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
actions:
  pre:
    preaction: echo 'pre' >> ${tmpa}/pre
    preaction2: echo 'pre2' >> ${tmpa}/pre2
  post:
    postaction: echo 'post' >> ${tmpa}/post
    postaction2: echo 'post2' >> ${tmpa}/post2
  nakedaction: echo 'naked' >> ${tmpa}/naked
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
  f_def:
    dst: ${tmpd}/def
    src: def
  f_ghi:
    dst: ${tmpd}/ghi
    src: ghi
profiles:
  p0:
    actions:
    - preaction2
    - postaction2
    - nakedaction
    dotfiles:
    - f_abc
    - f_def
    - f_ghi
_EOF
#cat ${cfg}

# create the dotfile
echo "test" > ${tmps}/dotfiles/abc
echo "test" > ${tmps}/dotfiles/def
echo "test" > ${tmps}/dotfiles/ghi

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p0 -V

# check actions executed
[ ! -e ${tmpa}/pre2 ] && echo 'action not executed' && exit 1
[ ! -e ${tmpa}/post2 ] && echo 'action not executed' && exit 1
[ ! -e ${tmpa}/naked ] && echo 'action not executed' && exit 1

grep pre2 ${tmpa}/pre2
nb=`wc -l ${tmpa}/pre2 | awk '{print $1}'`
[ "${nb}" != "1" ] && echo "profile action executed multiple times" && exit 1

grep post2 ${tmpa}/post2
nb=`wc -l ${tmpa}/post2 | awk '{print $1}'`
[ "${nb}" != "1" ] && echo "profile action executed multiple times" && exit 1

grep naked ${tmpa}/naked
nb=`wc -l ${tmpa}/naked | awk '{print $1}'`
[ "${nb}" != "1" ] && echo "profile action executed multiple times" && exit 1

# install again
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p0 -V

# check actions not executed twice
nb=`wc -l ${tmpa}/post2 | awk '{print $1}'`
[ "${nb}" -gt "1" ] && echo "action post2 executed twice" && exit 1
nb=`wc -l ${tmpa}/naked | awk '{print $1}'`
[ "${nb}" -gt "1" ] && echo "action naked executed twice" && exit 1

## CLEANING
rm -rf ${tmps} ${tmpd} ${tmpa}

echo "OK"
exit 0
