#!/usr/bin/env bash

version=$(git describe --tags --abbrev=0)

hash txt2man 2>/dev/null
[ "$?" != "0" ] && echo "install txt2man" && exit 1

txt2man \
  -t "dotdrop" \
  -P "dotdrop" \
  -r "dotdrop-${version}" \
  -s 1 \
  -v "Save your dotfiles once, deploy them everywhere" \
  dotdrop.txt2man > dotdrop.1
