#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test import duplicates
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
touch ${tmpd}/.colors
mkdir -p ${tmpd}/.mutt
touch ${tmpd}/.mutt/colors

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  longkey: false
dotfiles:
  f_colors:
    src: abc
    dst: abc
  f_mutt_colors:
    src: abc
    dst: abc
  f_`echo ${tmpd} | sed -e 's#^/\(.*\)$#\1#g' | sed 's#/#_#g' | tr '[:upper:]' '[:lower:]'`_colors:
    src: abc
    dst: abc
  f_`echo ${tmpd} | sed -e 's#^/tmp/\(.*\)$#\1#g' | sed 's#/#_#g' | tr '[:upper:]' '[:lower:]'`_colors:
    src: abc
    dst: abc
  f_`echo ${tmpd} | sed -e 's#^/\(.*\)$#\1#g' | sed 's#/#_#g' | tr '[:upper:]' '[:lower:]'`_mutt_colors:
    src: abc
    dst: abc
  f_`echo ${tmpd} | sed -e 's#^/tmp/\(.*\)$#\1#g' | sed 's#/#_#g' | tr '[:upper:]' '[:lower:]'`_mutt_colors:
    src: abc
    dst: abc
profiles:
_EOF
cat ${cfg}

# import
cd ${ddpath} | ${bin} import -c ${cfg} -p p1 -V ${tmpd}/.mutt/colors
cd ${ddpath} | ${bin} import -c ${cfg} -p p1 -V ${tmpd}/.colors

cat ${cfg}

# ensure exists and is not link
[ ! -d ${tmps}/dotfiles/${tmpd}/.mutt ] && echo "not a directory" && exit 1
[ ! -e ${tmps}/dotfiles/${tmpd}/.mutt/colors ] && echo "not exist" && exit 1
[ ! -e ${tmps}/dotfiles/${tmpd}/.colors ] && echo "not exist (2)" && exit 1

cat ${cfg} | grep ${tmpd}/.mutt/colors >/dev/null 2>&1
cat ${cfg} | grep ${tmpd}/.colors >/dev/null 2>&1

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
