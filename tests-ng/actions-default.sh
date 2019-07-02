#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test default action execution
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
    failpre: "false"
    preaction: echo 'pre' > ${tmpa}/pre
    preaction1: echo 'preinside' > ${tmpa}/preinside
  post:
    failpost: "false"
    postaction: echo 'post' > ${tmpa}/post
    postaction1: echo 'postinside' > ${tmpa}/postinside
  nakedaction: echo 'naked' > ${tmpa}/naked
  nakedaction1: echo 'nakedinside' > ${tmpa}/nakedinside
config:
  backup: true
  create: true
  dotpath: dotfiles
  default_actions:
  - preaction
  - postaction
  - nakedaction
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    actions:
      - preaction1
      - nakedaction1
      - postaction1
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

# checks pre action
[ ! -e ${tmpa}/pre ] && echo 'pre action not executed' && exit 1
[ ! -e ${tmpa}/preinside ] && echo 'pre action not executed' && exit 1
grep pre ${tmpa}/pre >/dev/null
grep preinside ${tmpa}/preinside >/dev/null
# checks post action
[ ! -e ${tmpa}/post ] && echo 'post action not executed' && exit 1
[ ! -e ${tmpa}/postinside ] && echo 'post action not executed' && exit 1
grep post ${tmpa}/post >/dev/null
grep postinside ${tmpa}/postinside >/dev/null
# checks naked action
[ ! -e ${tmpa}/naked ] && echo 'naked action not executed'  && exit 1
[ ! -e ${tmpa}/nakedinside ] && echo 'naked action not executed'  && exit 1
grep naked ${tmpa}/naked >/dev/null
grep nakedinside ${tmpa}/nakedinside >/dev/null

# clear
rm -f ${tmpa}/naked* ${tmpa}/pre* ${tmpa}/post* ${tmpd}/abc

cat > ${cfg} << _EOF
actions:
  pre:
    failpre: "false"
config:
  backup: true
  create: true
  dotpath: dotfiles
  default_actions:
  - failpre
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# ensure failing actions make the installation fail
# install
set +e
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V
set -e
[ -e ${tmpd}/abc ] && exit 1

## CLEANING
rm -rf ${tmps} ${tmpd} ${tmpa}

echo "OK"
exit 0
