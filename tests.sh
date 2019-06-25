#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

# stop on first error
set -ev

# PEP8 tests
which pycodestyle 2>/dev/null
[ "$?" != "0" ] && echo "Install pycodestyle" && exit 1
pycodestyle --ignore=W503,W504,W605 dotdrop/
pycodestyle tests/
pycodestyle scripts/

# pyflakes tests
pyflakes dotdrop/
pyflakes tests/

# retrieve the nosetests binary
set +e
nosebin="nosetests"
which ${nosebin} 2>/dev/null
[ "$?" != "0" ] && nosebin="nosetests3"
which ${nosebin} 2>/dev/null
[ "$?" != "0" ] && echo "Install nosetests" && exit 1
set -e

# execute tests with coverage
PYTHONPATH=dotdrop ${nosebin} -s --with-coverage --cover-package=dotdrop
#PYTHONPATH=dotdrop python3 -m pytest tests

## execute bash script tests
[ "$1" = '--python-only' ] || {
  log=`mktemp`
  for scr in tests-ng/*.sh; do
    ${scr} > "${log}" 2>&1 &
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
