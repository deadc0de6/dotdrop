#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test update of templates
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
echo "dotfiles source (dotpath): ${tmps}"
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
echo "dotfiles destination: ${tmpd}"
# the workdir
tmpw=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
echo "workdir: ${tmpw}"


# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  workdir: ${tmpw}
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
echo "head" > ${tmps}/dotfiles/abc
echo '{%@@ if profile == "p1" @@%}' >> ${tmps}/dotfiles/abc
echo "is p1" >> ${tmps}/dotfiles/abc
echo '{%@@ else @@%}' >> ${tmps}/dotfiles/abc
echo "is not p1" >> ${tmps}/dotfiles/abc
echo '{%@@ endif @@%}' >> ${tmps}/dotfiles/abc
echo "tail" >> ${tmps}/dotfiles/abc

# create the installed dotfile
echo "head" > ${tmpd}/abc
echo "is p1" >> ${tmpd}/abc
echo "tail" >> ${tmpd}/abc

# update
#cat ${tmps}/dotfiles/abc
set +e
patch=`cd ${ddpath} | ${bin} update -P -p p1 -k f_abc --cfg ${cfg} 2>&1 | grep 'try patching with' | sed 's/"//g'`
set -e
patch=`echo ${patch} | sed 's/^.*: //g'`
echo "patching with: ${patch}"
eval ${patch}
#cat ${tmps}/dotfiles/abc

## CLEANING
rm -rf ${tmps} ${tmpd} ${tmpw}

echo "OK"
exit 0
