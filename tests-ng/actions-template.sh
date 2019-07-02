#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test action template execution
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
    preaction: "echo {{@@ _dotfile_abs_src @@}} > {0}"
  post:
    postaction: "echo {{@@ _dotfile_abs_src @@}} > ${tmpa}/post"
  nakedaction: "echo {{@@ _dotfile_abs_src @@}} > ${tmpa}/naked"
config:
  backup: true
  create: true
  dotpath: dotfiles
  default_actions:
  - preaction "${tmpa}/pre"
  - postaction
  - nakedaction
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo 'test' > ${tmps}/dotfiles/abc

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

# checks action
[ ! -e ${tmpa}/pre ] && echo 'pre action not executed' && exit 1
[ ! -e ${tmpa}/post ] && echo 'post action not executed' && exit 1
[ ! -e ${tmpa}/naked ] && echo 'naked action not executed'  && exit 1
grep abc ${tmpa}/pre >/dev/null
grep abc ${tmpa}/post >/dev/null
grep abc ${tmpa}/naked >/dev/null

# clear
rm -f ${tmpa}/naked* ${tmpa}/pre* ${tmpa}/post* ${tmpd}/abc

cat > ${cfg} << _EOF
actions:
  pre:
    preaction: "echo {{@@ _dotfile_abs_dst @@}} > ${tmpa}/pre"
  post:
    postaction: "echo {{@@ _dotfile_abs_dst @@}} > ${tmpa}/post"
  nakedaction: "echo {{@@ _dotfile_abs_dst @@}} > ${tmpa}/naked"
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
      - nakedaction
      - postaction
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

# checks action
[ ! -e ${tmpa}/pre ] && echo 'pre action not executed' && exit 1
[ ! -e ${tmpa}/post ] && echo 'post action not executed' && exit 1
[ ! -e ${tmpa}/naked ] && echo 'naked action not executed'  && exit 1
grep "${tmpd}/abc" ${tmpa}/pre >/dev/null
grep "${tmpd}/abc" ${tmpa}/post >/dev/null
grep "${tmpd}/abc" ${tmpa}/naked >/dev/null

## CLEANING
rm -rf ${tmps} ${tmpd} ${tmpa}

echo "OK"
exit 0
