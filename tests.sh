#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

# stop on first error
set -ev

# PEP8 tests
which pycodestyle 2>/dev/null
[ "$?" != "0" ] && echo "Install pycodestyle" && exit 1
pycodestyle --ignore=W605 dotdrop/
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
for scr in tests-ng/*.sh; do
  ${scr}
done
