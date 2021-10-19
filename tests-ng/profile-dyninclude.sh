#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test profile dynvariables and included dynvariables
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

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"
cfg2="${tmps}/sub.yaml"

cat > ${cfg} << _EOF
config:
  dotpath: dotfiles
  import_configs:
  - sub.yaml
variables:
  mainvar: 'not-that'
  subvar: 'not-that-either'
dynvariables:
  maindyn: 'echo wont-work'
  subdyn: 'echo wont-work-either'
dotfiles:
profiles:
  profile_1:
    include:
    - subprofile
    dynvariables:
      maindyn: 'echo maindyncontent'
    variables:
      mainvar: 'maincontent'
  profile_2:
    include:
    - subignore
_EOF
#cat ${cfg}

cat > ${cfg2} << _EOF
config:
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
  f_def:
    dst: ${tmpd}/def
    src: def
  f_ghi:
    dst: '${tmpd}/{{@@ ghi @@}}'
    src: ghi
variables:
  mainvar: 'bad0'
  subvar: 'bad1'
dynvariables:
  maindyn: 'echo bad2'
  subdyn: 'echo bad3'
profiles:
  subprofile:
    dotfiles:
    - f_abc
    - f_ghi
    dynvariables:
      subdyn: 'echo subdyncontent'
      ghi: 'echo ghi'
    variables:
      subvar: 'subcontent'
  subignore:
    dotfiles:
    - f_def
_EOF
#cat ${cfg2}

# create the dotfile
echo "start" > ${tmps}/dotfiles/abc
echo "{{@@ mainvar @@}}" >> ${tmps}/dotfiles/abc
echo "{{@@ maindyn @@}}" >> ${tmps}/dotfiles/abc
echo "{{@@ subdyn @@}}" >> ${tmps}/dotfiles/abc
echo "{{@@ subvar @@}}" >> ${tmps}/dotfiles/abc
echo "end" >> ${tmps}/dotfiles/abc
#cat ${tmps}/dotfiles/abc
echo "ghi content" > ${tmps}/dotfiles/ghi

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p profile_1 --verbose

# check dotfile exists
[ ! -e ${tmpd}/abc ] && exit 1
grep 'maincontent' ${tmpd}/abc >/dev/null || (echo "variables 1 not resolved" && exit 1)
grep 'maindyncontent' ${tmpd}/abc >/dev/null || (echo "dynvariables 1 not resolved"  && exit 1)
grep 'subcontent' ${tmpd}/abc >/dev/null || (echo "variables 2 not resolved" && exit 1)
grep 'subdyncontent' ${tmpd}/abc >/dev/null || (echo "dynvariables 2 not resolved" && exit 1)
#cat ${tmpd}/abc
[ ! -e ${tmpd}/ghi ] && exit 1

echo "OK"
exit 0
