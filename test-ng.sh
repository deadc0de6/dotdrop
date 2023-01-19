#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6

# stop on first error
set -e

tmpworkdir="/tmp/dotdrop-tests-workdir"
export DOTDROP_WORKDIR="${tmpworkdir}"

workers=${DOTDROP_WORKERS}
if [ ! -z ${workers} ]; then
  DOTDROP_WORKERS=${workers}
  echo "ENABLE workers: ${workers}"
fi

# run bash tests
export DOTDROP_DEBUG="yes"
unset DOTDROP_FORCE_NODEBUG
workdir_tmp_exists="no"
[ -d "~/.config/dotdrop/tmp" ] && workdir_tmp_exists="yes"
if [ -z ${GITHUB_WORKFLOW} ]; then
  ## local
  export COVERAGE_FILE=
  tests-ng/tests-launcher.py
else
  ## CI/CD
  export COVERAGE_FILE="${cur}/.coverage"
  tests-ng/tests-launcher.py 1
fi

# clear workdir
[ "${workdir_tmp_exists}" = "no" ] && rm -rf ~/.config/dotdrop/tmp
# clear temp workdir
rm -rf "${tmpworkdir}"