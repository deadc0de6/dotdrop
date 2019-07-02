#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test variables per profile
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

# create a shell script
export TESTENV="this is my global testenv"
scr=`mktemp --suffix='-dotdrop-tests' || mktemp -d`
chmod +x ${scr}
echo -e "#!/bin/bash\necho $TESTENV\n" >> ${scr}

export TESTENV2="this is my profile testenv"
scr2=`mktemp --suffix='-dotdrop-tests' || mktemp -d`
chmod +x ${scr2}
echo -e "#!/bin/bash\necho $TESTENV2\n" >> ${scr2}

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
variables:
  gvar1: "global1"
  gvar2: "global2"
dynvariables:
  gdvar1: head -1 /proc/meminfo
  gdvar2: "echo 'this is some test' | rev | tr ' ' ','"
  gdvar3: ${scr}
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    variables:
      gvar1: "local1"
      lvar1: "local2"
    dynvariables:
      gdvar3: ${scr2}
      pdvar1: "echo 'abc' | rev"
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo "===================" > ${tmps}/dotfiles/abc
echo "{{@@ gvar1 @@}}" >> ${tmps}/dotfiles/abc
echo "{{@@ gvar2 @@}}" >> ${tmps}/dotfiles/abc
echo "{{@@ gdvar1 @@}}" >> ${tmps}/dotfiles/abc
echo "{{@@ gdvar2 @@}}" >> ${tmps}/dotfiles/abc
echo "{{@@ gdvar3 @@}}" >> ${tmps}/dotfiles/abc
echo "{{@@ lvar1 @@}}" >> ${tmps}/dotfiles/abc
echo "{{@@ pdvar1 @@}}" >> ${tmps}/dotfiles/abc
echo "===================" >> ${tmps}/dotfiles/abc

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

cat ${tmpd}/abc

# test variables
grep '^local1' ${tmpd}/abc >/dev/null
grep '^global2' ${tmpd}/abc >/dev/null
grep '^local2' ${tmpd}/abc >/dev/null
# test dynvariables
grep "^MemTotal" ${tmpd}/abc >/dev/null
grep '^tset,emos,si,siht' ${tmpd}/abc >/dev/null
grep "^${TESTENV2}" ${tmpd}/abc > /dev/null
grep "^cba" ${tmpd}/abc >/dev/null

#cat ${tmpd}/abc

## CLEANING
rm -rf ${tmps} ${tmpd} ${scr} ${scr2}

echo "OK"
exit 0
