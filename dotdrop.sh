#!/bin/bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

args="$@"
cur=`dirname $(readlink -f $0)`
opwd=`pwd`
bin="${cur}/dotdrop/dotdrop.py"

# run dotdrop
cfg="${cur}/config.yaml"
cd ${cur}
python3 ${bin} --cfg=${cfg} $args
cd ${opwd}
