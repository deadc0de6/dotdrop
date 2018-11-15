#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test transformations
# for install and compare
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

echo -e "\e[96m\e[1m==> RUNNING $(basename $BASH_SOURCE) <==\e[0m"

################################################################
# this is the test
################################################################

# the dotfile source
tmps=`mktemp -d`
mkdir -p ${tmps}/dotfiles
echo "dotfiles source (dotpath): ${tmps}"
# the dotfile destination
tmpd=`mktemp -d`
echo "dotfiles destination: ${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"

# token
token="test-base64"

cat > ${cfg} << _EOF
trans:
  base64: cat {0} | base64 -d > {1}
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_def:
    dst: ${tmpd}/def
    src: def
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    trans:
      - base64
profiles:
  p1:
    dotfiles:
    - f_abc
    - f_def
_EOF
cat ${cfg}

# create the dotfile
tmpf=`mktemp`
echo ${token}  > ${tmpf}
cat ${tmpf} | base64 > ${tmps}/dotfiles/abc
rm -f ${tmpf}

echo 'marker' > ${tmps}/dotfiles/def

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -b

# checks
[ ! -e ${tmpd}/abc ] && exit 1
content=`cat ${tmpd}/abc`
[ "${content}" != "${token}" ] && exit 1

# compare
cd ${ddpath} | ${bin} compare -c ${cfg} -p p1 -b
[ "$?" != "0" ] && exit 1

# change file
echo 'touched' >> ${tmpd}/abc
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} -p p1 -b
[ "$?" != "1" ] && exit 1
set -e

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
