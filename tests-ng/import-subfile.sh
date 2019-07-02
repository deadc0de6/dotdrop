#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test import file in directory
# after having imported directory
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

# create the dotfile
mkdir -p ${tmpd}/adir
echo "first" > ${tmpd}/adir/file1

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF
#cat ${cfg}

# import dir
cd ${ddpath} | ${bin} import -f -c ${cfg} -p p1 -V ${tmpd}/adir

# change the file
echo "second" >> ${tmpd}/adir/file1

# import file
cd ${ddpath} | ${bin} import -f -c ${cfg} -p p1 -V ${tmpd}/adir/file1

# test
#cat ${tmps}/dotfiles/${tmpd}/adir/file1
[ ! -e ${tmps}/dotfiles/${tmpd}/adir/file1 ] && echo "not exist" && exit 1
grep 'second' ${tmps}/dotfiles/${tmpd}/adir/file1 >/dev/null

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
