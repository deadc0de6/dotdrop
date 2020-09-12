#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

# stop on first error
set -ev

# PEP8 tests
which pycodestyle >/dev/null 2>&1
[ "$?" != "0" ] && echo "Install pycodestyle" && exit 1
echo "testing with pycodestyle"
pycodestyle --ignore=W503,W504,W605 dotdrop/
pycodestyle tests/
pycodestyle scripts/

# pyflakes tests
echo "testing with pyflakes"
pyflakes dotdrop/
pyflakes tests/

# retrieve the nosetests binary
nosebin="nosetests"
which ${nosebin} >/dev/null 2>&1
[ "$?" != "0" ] && nosebin="nosetests3"
which ${nosebin} >/dev/null 2>&1
[ "$?" != "0" ] && echo "Install nosetests" && exit 1

# do not print debugs when running tests (faster)
export DOTDROP_FORCE_NODEBUG=yes

# coverage file location
cur=`dirname $(readlink -f "${0}")`
export COVERAGE_FILE="${cur}/.coverage"

# execute tests with coverage
PYTHONPATH="dotdrop" ${nosebin} -s --with-coverage --cover-package=dotdrop
#PYTHONPATH="dotdrop" python3 -m pytest tests

# enable debug logs
export DOTDROP_DEBUG=
unset DOTDROP_FORCE_NODEBUG
# do not print debugs when running tests (faster)
#export DOTDROP_FORCE_NODEBUG=yes

## execute bash script tests
[ "$1" = '--python-only' ] || {
  echo "doing extended tests"
  log=`mktemp`
  for scr in tests-ng/*.sh; do
    if [ -z ${TRAVIS} ]; then
      ${scr} > "${log}" 2>&1 &
    else
      ${scr} > "${log}" >/dev/null 2>&1 &
    fi
    tail --pid="$!" -f "${log}"
    set +e
    wait "$!"
    if [ "$?" -ne 0 ]; then
        echo "Test ${scr} finished with error"
        rm -f ${log}
        exit 1
    elif grep Traceback ${log}; then
      echo "crash found in logs"
      rm -f ${log}
      exit 1
    fi
    set -e
  done
  rm -f ${log}
}

echo "All test finished successfully"
