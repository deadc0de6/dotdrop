#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

fold="dotfiles"
conf="config.yaml"

# copy dotdrop entry point
cp dotdrop/dotdrop.sh dotdrop.sh
chmod +x dotdrop.sh
mkdir -p $fold

if [ ! -e ${conf} ]; then
  # init config file
  cat << EOF > ${conf}
config:
  backup: true
  create: true
  dotpath: $fold
dotfiles:
profiles:
EOF
fi
