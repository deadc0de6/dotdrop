#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6

# stop on first error
set -eu -o errtrace -o pipefail

# ensure binaries are here
if ! which shellcheck >/dev/null 2>&1; then
  echo "Install shellcheck"
  exit 1
fi
echo "=> shellcheck version:"
shellcheck --version

# python tools versions
if ! which pylint >/dev/null 2>&1; then
  echo "Install pylint"
  exit 1
fi
echo "=> pylint version:"
pylint --version

if ! which pycodestyle >/dev/null 2>&1; then
  echo "Install pycodestyle"
  exit 1
fi
echo "=> pycodestyle version:"
pycodestyle --version

if ! which pyflakes >/dev/null 2>&1; then
  echo "Install pyflakes"
  exit 1
fi
echo "=> pyflakes version:"
pyflakes --version

# checking for TODO/FIXME
echo "--------------------------------------"
echo "checking for TODO/FIXME"
set +e
grep -r 'TODO\|FIXME' dotdrop/ && exit 1
grep -r 'TODO\|FIXME' tests/ && exit 1
grep -r 'TODO\|FIXME' tests-ng/ && exit 1
#grep -r 'TODO\|FIXME' scripts/ && exit 1
set -e

# checking for tests options
echo "---------------------------------"
echo "checking for bash strict mode"
find tests-ng -iname '*.sh' | while read -r script; do
  #grep 'set +e' "${script}" 2>&1 >/dev/null && echo "set +e found in ${script}" && exit 1
  grep 'set -eu -o errtrace -o pipefail' "${script}" >/dev/null 2>&1 || \
    (echo "\"set -eu -o errtrace -o pipefail\" not set in ${script}" && exit 1 )
done

# PEP8 tests
# W503: Line break occurred before a binary operator
# W504: Line break occurred after a binary operator
echo "---------------------------------"
echo "checking dotdrop with pycodestyle"
pycodestyle --ignore=W503,W504 dotdrop/
pycodestyle scripts/

# pyflakes tests
echo "------------------------------"
echo "checking dotdrop with pyflakes"
pyflakes dotdrop/

# pylint
echo "----------------------------"
echo "checking dotdrop with pylint"
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

# check shell scripts
# SC2002: Useless cat
# SC2126: Consider using grep -c instead of grep|wc -l
# SC2129: Consider using { cmd1; cmd2; } >> file instead of individual redirects
# SC2181: Check exit code directly with e.g. 'if mycmd;', not indirectly with $?
# SC1004: This backslash+linefeed is literal. Break outside single quotes if you just want to break the line
echo "--------------------------------------"
echo "checking shell scripts with shellcheck"
find . -iname '*.sh' | while read -r script; do
  echo "checking ${script}"
  shellcheck -x \
    -e SC2002 \
    -e SC2126 \
    -e SC2129 \
    -e SC2181 \
    -e SC1004 \
    -e SC1117 \
    -e SC2230 \
    "${script}"
done

# check other python scripts
echo "-----------------------------------------"
echo "checking other python scripts with pylint"
find . -name "*.py" -not -path "./dotdrop/*" -not -regex "\./\.?v?env/.*" | while read -r script; do
  echo "checking ${script}"
  pylint -sn \
    --disable=R0914 \
    --disable=R0915 \
    --disable=R0913 \
    "${script}"
done

echo "------------------------"
echo "checking for more issues"
exceptions="save_uservariables_name\|@@\|diff_cmd\|original,\|modified,"
# f-string errors and missing f literal
find dotdrop/ -iname '*.py' -exec grep --with-filename -n -v "f'" {} \; | grep -v "{'" | grep -v "${exceptions}" | grep "'.*}" && echo "bad string format (1)" && exit 1
find dotdrop/ -iname '*.py' -exec grep --with-filename -n -v 'f"' {} \; | grep -v "f'" | grep -v '{"' | grep -v "${exceptions}" | grep '".*}' && echo "bad string format (2)" && exit 1

echo "syntax OK"