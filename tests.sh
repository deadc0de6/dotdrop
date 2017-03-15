#!/bin/bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

# stop on first error
set -ev

pep8 dotdrop/
pep8 tests/
PYTHONPATH=dotdrop nosetests -w tests
