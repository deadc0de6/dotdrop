#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6

# stop on first error
#set -ev
set -e

# versions
echo "pylint version:"
pylint --version
echo "pycodestyle version:"
pycodestyle --version
echo "pyflakes version:"
pyflakes --version

# PEP8 tests
which pycodestyle >/dev/null 2>&1
[ "$?" != "0" ] && echo "Install pycodestyle" && exit 1
echo "testing with pycodestyle"
# W503: Line break occurred before a binary operator
# W504: Line break occurred after a binary operator
pycodestyle --ignore=W503,W504 dotdrop/
pycodestyle tests/
pycodestyle scripts/

# pyflakes tests
echo "testing with pyflakes"
pyflakes dotdrop/
pyflakes tests/
pyflakes scripts/

# pylint
echo "testing with pylint"
# https://pylint.pycqa.org/en/latest/user_guide/checkers/features.html
# R0902: too-many-instance-attributes
# R0913: too-many-arguments
# R0903: too-few-public-methods
# R0914: too-many-locals
# R0915: too-many-statements
# R0912: too-many-branches
# R0911: too-many-return-statements
# R0904: too-many-public-methods
pylint \
  --disable=R0902 \
  --disable=R0913 \
  --disable=R0903 \
  --disable=R0914 \
  --disable=R0915 \
  --disable=R0912 \
  --disable=R0911 \
  --disable=R0904 \
  dotdrop/

# C0103: invalid-name
pylint \
  --disable=R0902 \
  --disable=R0913 \
  --disable=R0903 \
  --disable=R0914 \
  --disable=R0915 \
  --disable=R0912 \
  --disable=R0911 \
  --disable=R0904 \
  --disable=C0103 \
  scripts/

set +e
exceptions="save_uservariables_name\|@@\|diff_cmd\|original,\|modified,"
# f-string errors and missing f literal
find dotdrop/ -iname '*.py' -exec grep --with-filename -n -v "f'" {} \; | grep -v "{'" | grep -v "${exceptions}" | grep "'.*}" && echo "bad string format (1): ${errs}" && exit 1
find dotdrop/ -iname '*.py' -exec grep --with-filename -n -v 'f"' {} \; | grep -v "f'" | grep -v '{"' | grep -v "${exceptions}" | grep '".*}' && echo "bad string format (2): ${errs}" && exit 1
set -e

echo "syntax OK"