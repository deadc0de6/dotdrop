#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test importing and updating entire directories
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

# dotdrop directory
basedir=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
dotfiles="${basedir}/dotfiles"
echo "dotdrop dir: ${basedir}"
# the dotfile
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
create_dir ${tmpd}

# create the config file
cfg="${basedir}/config.yaml"
create_conf ${cfg} # sets token

# import the dir
cd ${ddpath} | ${bin} import -c ${cfg} ${tmpd}

# change token
echo "changed" > ${token}

# update
cd ${ddpath} | ${bin} update -f -c ${cfg} ${tmpd} --verbose

grep 'changed' ${token} >/dev/null 2>&1

## CLEANING
rm -rf ${basedir} ${tmpd}

echo "OK"
exit 0
