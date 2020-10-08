#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2020, deadc0de6
#
# test notemplate
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

# globally
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  template_dotfile_default: true
dotfiles:
  d_d1:
    dst: ${tmpd}/d1
    src: d1
profiles:
  p1:
    dotfiles:
    - d_d1
_EOF
#cat ${cfg}

# create the dotfile
echo "before" > ${tmps}/dotfiles/d1
echo "{#@@ should not be stripped @@#}" >> ${tmps}/dotfiles/d1
echo "{{@@ header() @@}}" >> ${tmps}/dotfiles/d1
echo "after" >> ${tmps}/dotfiles/d1

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

# test existence
[ ! -e ${tmpd}/d1 ] && echo 'not installed' && exit 1
grep 'header' ${tmpd}/d1 || echo "header stripped" && exit 1
grep 'should not be stripped' ${tmpd}/d1 || echo "comment stripped" && exit 1

# through the dotfile
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  d_d1:
    dst: ${tmpd}/d1
    src: d1
    notemplate: true
profiles:
  p1:
    dotfiles:
    - d_d1
_EOF
#cat ${cfg}

# clean destination
rm -rf ${tmpd}/*

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

# test existence
[ ! -e ${tmpd}/d1 ] && echo 'not installed' && exit 1
grep 'header' ${tmpd}/d1 || echo "header stripped" && exit 1
grep 'should not be stripped' ${tmpd}/d1 || echo "comment stripped" && exit 1

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
