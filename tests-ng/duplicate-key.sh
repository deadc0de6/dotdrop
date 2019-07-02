#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test duplicate keys
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

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
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

# create the imported one
mkdir -p ${tmps}/dotfiles/${tmpd}
echo "test" > ${tmps}/dotfiles/${tmpd}/abc
echo "test" > ${tmpd}/abc

# create the to-be-imported
mkdir -p ${tmpd}/sub
echo "test2" > ${tmpd}/sub/abc

mkdir -p ${tmpd}/sub/sub2
echo "test2" > ${tmpd}/sub/sub2/abc

mkdir -p ${tmpd}/sub/sub
echo "test2" > ${tmpd}/sub/sub/abc

# import
cd ${ddpath} | ${bin} import -c ${cfg} -p p2 \
  ${tmpd}/abc \
  ${tmpd}/sub/abc \
  ${tmpd}/sub/abc \
  ${tmpd}/sub/sub/abc \
  ${tmpd}/sub/sub2/abc

# count dotfiles for p2
cnt=`cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p2 -b | grep '^f_' | wc -l`
[ "${cnt}" != "4" ] && exit 1

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
