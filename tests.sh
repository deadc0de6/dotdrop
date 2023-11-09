#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

# stop on first error
set -eu -o errtrace -o pipefail

cur=$(cd "$(dirname "${0}")" && pwd)

# make sure both version.py and manpage dotdrop.1 are in sync
dotdrop_version=$(grep version dotdrop/version.py | sed 's/^.*= .\(.*\).$/\1/g')
man_version=$(grep '^\.TH' manpage/dotdrop.1  | sed 's/^.*"dotdrop-\(.*\)\" "Save your.*$/\1/g')
if [ "${dotdrop_version}" != "${man_version}" ]; then
  echo "ERROR version.py (${dotdrop_version}) and manpage (${man_version}) differ!"
  exit 1
fi
echo "current dotdrop version ${dotdrop_version}"

echo "=> python version:"
python3 --version

# test syntax
echo "checking syntax..."
"${cur}"/scripts/check-syntax.sh

# unittest
echo "unittest..."
"${cur}"/scripts/check-unittests.sh

# tests-ng
echo "tests-ng..."
"${cur}"/scripts/check-tests-ng.sh

# merge coverage
coverage combine coverages/*

# test doc
echo "checking documentation..."
"${cur}"/scripts/check-doc.sh

## done
echo "All tests finished successfully"
