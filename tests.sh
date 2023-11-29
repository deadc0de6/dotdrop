#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

# stop on first error
set -eu -o errtrace -o pipefail

cur=$(cd "$(dirname "${0}")" && pwd)
in_cicd="${GH_WORKFLOW:-}"

# patch TERM var in ci/cd
if [ -n "${in_cicd}" ]; then
  if [ -z "${TERM}" ]; then
    export TERM="linux"
  fi
fi

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
if [ -n "${in_cicd}" ]; then
  # in CI/CD
  export DOTDROP_WORKERS=1
  echo "tests-ng with ${DOTDROP_WORKERS} worker(s)..."
  "${cur}"/scripts/check-tests-ng.sh

  export DOTDROP_WORKERS=4
  echo "tests-ng with ${DOTDROP_WORKERS} worker(s)..."
  "${cur}"/scripts/check-tests-ng.sh
else
  echo "tests-ng..."
  "${cur}"/scripts/check-tests-ng.sh
fi

# merge coverage
coverage combine coverages/*
coverage xml

# test doc
echo "checking documentation..."
"${cur}"/scripts/check-doc.sh

## done
echo "All tests finished successfully"
