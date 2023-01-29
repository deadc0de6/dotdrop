#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6

# stop on first error
set -e

rl="readlink -f"
if ! ${rl} "${0}" >/dev/null 2>&1; then
  rl="realpath"

  if ! hash ${rl}; then
    echo "\"${rl}\" not found!" && exit 1
  fi
fi
cur=$(dirname "$(${rl} "${0}")")

if [ -n "${DOTDROP_WORKERS}" ]; then
  unset DOTDROP_WORKERS
  echo "DISABLE workers for unittests"
fi

coverage run -p -m pytest tests