#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6

# stop on first error
set -eu -o errtrace -o pipefail

tmpworkdir="/tmp/dotdrop-tests-workdir"
export DOTDROP_WORKDIR="${tmpworkdir}"

# check if tmp dir is present
workdir_tmp_exists="no"
[ -d "${HOME}/.config/dotdrop/tmp" ] && workdir_tmp_exists="yes"

# run bash tests
in_cicd=${GITHUB_WORKFLOW:-}
if [ -z "${in_cicd}" ]; then
  ## local
  tests-ng/tests_launcher.py -s
else
  ## CI/CD
  # running multiple jobs in parallel sometimes
  # messes with the results on remote servers
  tests-ng/tests_launcher.py -p 1 -n -s
fi

# clear workdir
[ "${workdir_tmp_exists}" = "no" ] && rm -rf ~/.config/dotdrop/tmp
# clear temp workdir
rm -rf "${tmpworkdir}"

echo "tests-ng done"