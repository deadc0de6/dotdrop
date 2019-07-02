#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test dynamic actions
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
variables:
  var1: "var1"
  var2: "{{@@ var1 @@}} var2"
  var3: "{{@@ var2 @@}} var3"
  var4: "{{@@ dvar4 @@}}"
dynvariables:
  dvar1: "echo dvar1"
  dvar2: "{{@@ dvar1 @@}} dvar2"
  dvar3: "{{@@ dvar2 @@}} dvar3"
  dvar4: "echo {{@@ var3 @@}}"
actions:
  pre:
    preaction1: "echo {{@@ var3 @@}} > ${tmpa}/preaction1"
    preaction2: "echo {{@@ dvar3 @@}} > ${tmpa}/preaction2"
  post:
    postaction1: "echo {{@@ var3 @@}} > ${tmpa}/postaction1"
    postaction2: "echo {{@@ dvar3 @@}} > ${tmpa}/postaction2"
  naked1: "echo {{@@ var3 @@}} > ${tmpa}/naked1"
  naked2: "echo {{@@ dvar3 @@}} > ${tmpa}/naked2"
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    actions:
      - preaction1
      - preaction2
      - postaction1
      - postaction2
      - naked1
      - naked2
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo "test" > ${tmps}/dotfiles/abc

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 --verbose

# checks
[ ! -e ${tmpa}/preaction1 ] && exit 1
[ ! -e ${tmpa}/preaction2 ] && exit 1
[ ! -e ${tmpa}/postaction1 ] && exit 1
[ ! -e ${tmpa}/postaction2 ] && exit 1
[ ! -e ${tmpa}/naked1 ] && exit 1
[ ! -e ${tmpa}/naked2 ] && exit 1

grep 'var1 var2 var3' ${tmpa}/preaction1 >/dev/null
grep 'dvar1 dvar2 dvar3' ${tmpa}/preaction2 >/dev/null
grep 'var1 var2 var3' ${tmpa}/postaction1 >/dev/null
grep 'dvar1 dvar2 dvar3' ${tmpa}/postaction2 >/dev/null
grep 'var1 var2 var3' ${tmpa}/naked1 >/dev/null
grep 'dvar1 dvar2 dvar3' ${tmpa}/naked2 >/dev/null

## CLEANING
rm -rf ${tmps} ${tmpd} ${tmpa}

echo "OK"
exit 0
