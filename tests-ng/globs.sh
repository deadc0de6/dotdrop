#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# ensure imports allow globs
# - import_actions
# - import_configs
# - import_variables
# - profile import
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
# temporary
tmpa=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`

###########
# test globs in import_actions
###########
# create the action files
actionsd="${tmps}/actions"
mkdir -p ${actionsd}
cat > ${actionsd}/action1.yaml << _EOF
actions:
  fromaction1: echo "fromaction1" > ${tmpa}/fromaction1
_EOF
cat > ${actionsd}/action2.yaml << _EOF
actions:
  fromaction2: echo "fromaction2" > ${tmpa}/fromaction2
_EOF

cfg="${tmps}/config.yaml"
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_actions:
  - ${actionsd}/*
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    actions:
      - fromaction1
      - fromaction2
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# create the source
mkdir -p ${tmps}/dotfiles/
echo "abc" > ${tmps}/dotfiles/abc

# install
cd ${ddpath} | ${bin} install -c ${cfg} -p p1 -V

# checks
[ ! -e ${tmpd}/abc ] && echo "dotfile not installed" && exit 1
[ ! -e  ${tmpa}/fromaction1 ] && echo "action1 not executed" && exit 1
grep fromaction1 ${tmpa}/fromaction1
[ ! -e  ${tmpa}/fromaction2 ] && echo "action2 not executed" && exit 1
grep fromaction2 ${tmpa}/fromaction2

## CLEANING
rm -rf ${tmps} ${tmpd} ${tmpa}

echo "OK"
exit 0
