#!/bin/bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

fold="dotfiles"

# copy dotdrop entry point
cat dotdrop/dotdrop.sh | sed 's#${cur}/dotdrop/dotdrop.py#${cur}/dotdrop/dotdrop/dotdrop.py#g' > dotdrop.sh
chmod +x dotdrop.sh
mkdir $fold

# init config file
cat << EOF > config.yaml
config:
  backup: true
  create: true
  dotpath: $fold
dotfiles:
profiles:
EOF
