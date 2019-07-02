#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# import config testing
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
cfg1="${tmps}/config1.yaml"
cfg2="${tmps}/config2.yaml"

cat > ${cfg1} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_configs:
  - ${cfg2}
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
  f_zzz:
    dst: ${tmpd}/zzz
    src: zzz
  f_sub:
    dst: ${tmpd}/sub
    src: sub
profiles:
  p0:
    include:
    - p2
  p1:
    dotfiles:
    - f_abc
  p3:
    dotfiles:
    - f_zzz
  pup:
    include:
    - psubsub
_EOF

cat > ${cfg2} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_def:
    dst: ${tmpd}/def
    src: def
  f_ghi:
    dst: ${tmpd}/ghi
    src: ghi
profiles:
  p2:
    dotfiles:
    - f_def
  psubsub:
    dotfiles:
    - f_sub
_EOF

# create the source
mkdir -p ${tmps}/dotfiles/
echo "abc" > ${tmps}/dotfiles/abc
echo "def" > ${tmps}/dotfiles/def
echo "ghi" > ${tmps}/dotfiles/ghi
echo "zzz" > ${tmps}/dotfiles/zzz
echo "sub" > ${tmps}/dotfiles/sub

# install
cd ${ddpath} | ${bin} listfiles -c ${cfg1} -p p0 -V | grep f_def
cd ${ddpath} | ${bin} listfiles -c ${cfg1} -p p1 -V | grep f_abc
cd ${ddpath} | ${bin} listfiles -c ${cfg1} -p p2 -V | grep f_def
cd ${ddpath} | ${bin} listfiles -c ${cfg1} -p p3 -V | grep f_zzz
cd ${ddpath} | ${bin} listfiles -c ${cfg1} -p pup -V | grep f_sub
cd ${ddpath} | ${bin} listfiles -c ${cfg1} -p psubsub -V | grep f_sub

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
