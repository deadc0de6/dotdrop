#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test pre/post/naked actions
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

# the action temp
tmpa=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
# the dotfile source
tmps=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
mkdir -p ${tmps}/dotfiles
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
actions:
  pre:
    preaction: echo 'pre' > ${tmpa}/pre
    preaction2: echo 'pre2' > ${tmpa}/pre2
  post:
    postaction: echo 'post' > ${tmpa}/post
    postaction2: echo 'post2' > ${tmpa}/post2
  nakedaction: echo 'naked' > ${tmpa}/naked
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    actions:
      - preaction
      - postaction
      - nakedaction
      - preaction2
      - postaction2
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo "test" > ${tmps}/dotfiles/abc

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

# checks
[ ! -e ${tmpa}/pre ] && exit 1
grep pre ${tmpa}/pre >/dev/null
[ ! -e ${tmpa}/post ] && exit 1
grep post ${tmpa}/post >/dev/null
[ ! -e ${tmpa}/naked ] && exit 1
grep naked ${tmpa}/naked >/dev/null
[ ! -e ${tmpa}/pre2 ] && exit 1
grep pre2 ${tmpa}/pre2 >/dev/null
[ ! -e ${tmpa}/post2 ] && exit 1
grep post2 ${tmpa}/post2 >/dev/null

## CLEANING
rm -rf ${tmps} ${tmpd} ${tmpa}

echo "OK"
exit 0
