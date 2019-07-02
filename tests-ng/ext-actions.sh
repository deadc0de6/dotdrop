#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test external actions
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

act="${tmps}/actions.yaml"
cat > ${act} << _EOF
actions:
  pre:
    preaction: echo 'pre' > ${tmpa}/pre
  post:
    postaction: echo 'post' > ${tmpa}/post
  nakedaction: echo 'naked' > ${tmpa}/naked
  overwrite: echo 'over' > ${tmpa}/write
_EOF

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_actions:
  - ${tmps}/actions.yaml
actions:
  overwrite: echo 'write' > ${tmpa}/write
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    actions:
      - preaction
      - postaction
      - nakedaction
      - overwrite
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
echo "pre is ok"

[ ! -e ${tmpa}/post ] && exit 1
grep post ${tmpa}/post >/dev/null
echo "post is ok"

[ ! -e ${tmpa}/naked ] && exit 1
grep naked ${tmpa}/naked >/dev/null
echo "naked is ok"

[ ! -e ${tmpa}/write ] && exit 1
grep over ${tmpa}/write >/dev/null
echo "write is ok"

## CLEANING
rm -rf ${tmps} ${tmpd} ${tmpa}

echo "OK"
exit 0
