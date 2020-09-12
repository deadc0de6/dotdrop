#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test variables defined in a different profile
# than the one selected
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
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
#echo "dotfile destination: ${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: "${tmpd}/{{@@ defined_in_main @@}}"
    src: abc
  f_def:
    dst: "${tmpd}/{{@@ defined_in_alt @@}}"
    src: def
profiles:
  pmain:
    dynvariables:
      defined_in_main: echo abc
    dotfiles:
    - f_abc
  palt:
    dynvariables:
      defined_in_alt: echo def
    dotfiles:
    - f_def
  pall:
    dynvariables:
      defined_in_main: echo abcall
      defined_in_alt: echo defall
    dotfiles:
    - ALL
  pinclude:
    include:
    - pmain
_EOF
#cat ${cfg}

# create the dotfile
echo "main" > ${tmps}/dotfiles/abc
echo "alt" > ${tmps}/dotfiles/def

# install pmain
echo "install pmain"
cd ${ddpath} | ${bin} install -f -c ${cfg} -p pmain -V
[ ! -e ${tmpd}/abc ] && echo "dotfile not installed" && exit 1
grep main ${tmpd}/abc

# install pall
echo "install pall"
cd ${ddpath} | ${bin} install -f -c ${cfg} -p pall -V
[ ! -e ${tmpd}/abcall ] && echo "dotfile not installed" && exit 1
grep main ${tmpd}/abcall
[ ! -e ${tmpd}/defall ] && echo "dotfile not installed" && exit 1
grep alt ${tmpd}/defall

# install pinclude
echo "install pinclude"
rm -f ${tmpd}/abc
cd ${ddpath} | ${bin} install -f -c ${cfg} -p pinclude -V
[ ! -e ${tmpd}/abc ] && echo "dotfile not installed" && exit 1
grep main ${tmpd}/abc

## CLEANING
rm -rf ${tmps} ${tmpd} ${scr} ${scr2}

echo "OK"
exit 0
