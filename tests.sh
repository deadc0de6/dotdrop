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
cur=$(dirname "$(${rl} "${0}")")

# make sure both version.py and manpage dotdrop.1 are in sync
dotdrop_version=$(grep version dotdrop/version.py | sed 's/^.*= .\(.*\).$/\1/g')
man_version=$(grep '^\.TH' manpage/dotdrop.1  | sed 's/^.*"dotdrop-\(.*\)\" "Save your.*$/\1/g')
if [ "${dotdrop_version}" != "${man_version}" ]; then
  echo "ERROR version.py (${dotdrop_version}) and manpage (${man_version}) differ!"
  exit 1
fi
echo "current version ${dotdrop_version}"

# test syntax
echo "checking syntax..."
"${cur}"/test-syntax.sh

# test doc
echo "checking documentation..."
"${cur}"/test-doc.sh

# unittest
echo "unittest..."
"${cur}"/test-unittest.sh

# tests-ng
echo "tests-ng..."
"${cur}"/test-ng.sh

## done
echo "All tests finished successfully"
