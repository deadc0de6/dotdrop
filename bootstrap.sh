#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

conf="config.yaml"

# copy dotdrop entry point
cp dotdrop/dotdrop.sh dotdrop.sh
chmod +x dotdrop.sh
mkdir -p dotfiles

if [ ! -e "${conf}" ]; then
  # init config file
  ./dotdrop.sh gencfg > "${conf}"
fi
