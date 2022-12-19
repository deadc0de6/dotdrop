#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

# stop on first error
#set -ev
set -e

rl="readlink -f"
if ! ${rl} "${0}" >/dev/null 2>&1; then
  rl="realpath"

  if ! hash ${rl}; then
    echo "\"${rl}\" not found!" && exit 1
  fi
fi
cur=`dirname $(${rl} "${0}")`

# test syntax
${cur}/test-syntax.sh

# test doc
${cur}/test-doc.sh

workers=${DOTDROP_WORKERS}
if [ ! -z ${workers} ]; then
  unset DOTDROP_WORKERS
  echo "DISABLE workers"
fi

# execute tests with coverage
if [ -z ${GITHUB_WORKFLOW} ]; then
  ## local
  export COVERAGE_FILE=
  # do not print debugs when running tests (faster)
  # tests
  PYTHONPATH="dotdrop" nose2 --with-coverage --coverage dotdrop --plugin=nose2.plugins.mp -N0
else
  ## CI/CD
  export COVERAGE_FILE="${cur}/.coverage"
  # tests
  PYTHONPATH="dotdrop" nose2 --with-coverage --coverage dotdrop
fi
#PYTHONPATH="dotdrop" python3 -m pytest tests

tmpworkdir="/tmp/dotdrop-tests-workdir"
export DOTDROP_WORKDIR="${tmpworkdir}"

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

## done
echo "All test finished successfully"
