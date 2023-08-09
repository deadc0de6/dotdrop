#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6

# stop on first error
set -e

if [ -n "${DOTDROP_WORKERS}" ]; then
  unset DOTDROP_WORKERS
  echo "DISABLE workers for unittests"
fi

mkdir -p coverages/
coverage run -p --data-file coverages/coverage -m pytest tests