#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

args="$@"
cur=`dirname $(readlink -f $0)`
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
