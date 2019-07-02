#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test recursive include
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
  f_def:
    dst: ${tmpd}/def
    src: def
profiles:
  host:
    include:
    - user
  common:
    dotfiles:
    - f_def
  user:
    dotfiles:
    - f_abc
    include:
    - common
_EOF

# create the source
mkdir -p ${tmps}/dotfiles/
content_abc="testrecinclude_abc"
echo "${content_abc}" > ${tmps}/dotfiles/abc
content_def="testrecinclude_def"
echo "${content_def}" > ${tmps}/dotfiles/def

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p host -V

# checks
[ ! -e ${tmpd}/abc ] && echo "abc not installed" && exit 1
echo "abc installed"
grep ${content_abc} ${tmpd}/abc

[ ! -e ${tmpd}/def ] && echo "def not installed" && exit 1
echo "def installed"
grep ${content_def} ${tmpd}/def

# test cyclic include
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
  f_def:
    dst: ${tmpd}/def
    src: def
profiles:
  host:
    include:
    - user
  common:
    include:
    - host
    dotfiles:
    - f_def
  user:
    dotfiles:
    - f_abc
    include:
    - common
_EOF

# install
set +e
cd ${ddpath} | ${bin} install -f -c ${cfg} -p host -V
[ "$?" = 0 ] && exit 1
set -e

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
