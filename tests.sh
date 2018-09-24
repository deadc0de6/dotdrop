#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

# stop on first error
set -ev

pycodestyle --ignore=W605 dotdrop/
pycodestyle tests/
pycodestyle scripts/

# travis
PYTHONPATH=dotdrop nosetests --with-coverage --cover-package=dotdrop
# arch / debian
#PYTHONPATH=dotdrop python3 -m nose --with-coverage --cover-package=dotdrop
# others
#PYTHONPATH=dotdrop nosetests -s --with-coverage --cover-package=dotdrop

# execute bash script tests
for scr in tests-ng/*.sh; do
  ${scr}
done
