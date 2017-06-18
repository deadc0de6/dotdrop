#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

# check for readlink/realpath presence
# https://github.com/deadc0de6/dotdrop/issues/6
rl="readlink -f"
${rl} >/dev/null 2>&1
if [ "$?" != "0" ]; then
  rl="realpath"
  hash ${rl}
  [ "$?" != "0" ] && echo "\"${rl}\" not found !" && exit 1
fi

# setup variables
args="$@"
cur=`dirname $(${rl} ${0})`
opwd=`pwd`
bin="${cur}/dotdrop/dotdrop.py"
cfg="${cur}/config.yaml"

# pivot
cd ${cur}
# init the submodule
git submodule update --init --recursive
# launch dotdrop
python3 ${bin} --cfg=${cfg} $args
# pivot back
cd ${opwd}
