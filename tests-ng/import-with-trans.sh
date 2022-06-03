#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6
#
# test transformations for import
# returns 1 in case of error
#

# exit on first error
set -e
#set -v

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
echo "dotfiles source (dotpath): ${tmps}"
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
echo "dotfiles destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
trans_read:
  base64: cat {0} | base64 -d > {1}
  uncompress: mkdir -p {1} && tar -xf {0} -C {1}
trans_write:
  base64: cat {0} | base64 > {1}
  compress: tar -cf {1} -C {0} .
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF
#cat ${cfg}

# tokens
token="test-base64"
tokend="compressed archive"

# create the dotfiles
echo ${token} > ${tmpd}/abc
mkdir -p ${tmpd}/def/a
echo ${tokend} > ${tmpd}/def/a/file

###########################
# test import
###########################

echo "[+] run import"
# import file
cd ${ddpath} | ${bin} import -f -c ${cfg} -p p1 -b -V -S base64 ${tmpd}/abc
# import directory
cd ${ddpath} | ${bin} import -f -c ${cfg} -p p1 -b -V -S compress ${tmpd}/def

# check file imported in dotpath
[ ! -e ${tmps}/dotfiles/${tmpd}/abc ] && echo "abc does not exist" && exit 1
[ ! -e ${tmps}/dotfiles/${tmpd}/def ] && echo "def does not exist" && exit 1

# check content in dotpath
echo "checking content"
file ${tmps}/dotfiles/${tmpd}/abc | grep -i 'text'
cat ${tmpd}/abc | base64 > ${tmps}/test-abc
diff ${tmps}/dotfiles/${tmpd}/abc ${tmps}/test-abc

file ${tmps}/dotfiles/${tmpd}/def | grep -i 'tar'
tar -cf ${tmps}/test-def -C ${tmpd}/def .
diff ${tmps}/dotfiles/${tmpd}/def ${tmps}/test-def

# check is imported in config
echo "checking imported in config"
cd ${ddpath} | ${bin} -p p1 -c ${cfg} files
cd ${ddpath} | ${bin} -p p1 -c ${cfg} files | grep '^f_abc'
cd ${ddpath} | ${bin} -p p1 -c ${cfg} files | grep '^d_def'

# check has trans_write in config
echo "checking trans_write is set in config"
cat ${cfg}
cat ${cfg} | grep -m 1 -A 3 'f_abc' | grep 'trans_write: base64'
cat ${cfg} | grep -m 1 -A 3 'd_def' | grep 'trans_write: compress'

echo "OK"
exit 0
