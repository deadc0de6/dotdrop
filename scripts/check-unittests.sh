#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6

# stop on first error
set -euo errtrace pipefail

WORKERS=${DOTDROP_WORKERS:-}
if [ -n "${WORKERS}" ]; then
  unset DOTDROP_WORKERS
  echo "DISABLE workers for unittests"
fi

mkdir -p coverages/
coverage run -p --data-file coverages/coverage -m pytest tests -x