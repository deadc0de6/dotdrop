#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test variables from yaml file
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
hash coverage 2>/dev/null && bin="coverage run -a --source=dotdrop -m dotdrop.dotdrop" || true

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
#echo "dotfile source: ${tmps}"
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
#echo "dotfile destination: ${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"
export dotdrop_test_dst="${tmpd}/def"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
variables:
  var1: "this is some test"
  var2: 12
  var3: another test
  vardst: "{{@@ env['dotdrop_test_dst'] @@}}"
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
  f_def:
    dst: "{{@@ vardst @@}}"
    src: def
profiles:
  p1:
    dotfiles:
    - f_abc
    - f_def
_EOF
#cat ${cfg}

# create the dotfile
echo "{{@@ var1 @@}}" > ${tmps}/dotfiles/abc
echo "{{@@ var2 @@}}" >> ${tmps}/dotfiles/abc
echo "{{@@ var3 @@}}" >> ${tmps}/dotfiles/abc
echo "test" >> ${tmps}/dotfiles/abc

echo "test_def" > ${tmps}/dotfiles/def

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 --verbose

[ ! -e ${tmpd}/abc ] && echo "abc not installed" && exit 1
grep '^this is some test' ${tmpd}/abc >/dev/null
grep '^12' ${tmpd}/abc >/dev/null
grep '^another test' ${tmpd}/abc >/dev/null

[ ! -e ${tmpd}/def ] && echo "def not installed" && exit 1
grep '^test_def' ${tmpd}/def >/dev/null

#cat ${tmpd}/abc

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
