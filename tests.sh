#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

# stop on first error
set -ev

pycodestyle dotdrop/
pycodestyle tests/
PYTHONPATH=dotdrop nosetests --with-coverage --cover-package=dotdrop
#PYTHONPATH=dotdrop nosetests -s --with-coverage --cover-package=dotdrop
#PYTHONPATH=dotdrop python3 -m nose --with-coverage --cover-package=dotdrop
