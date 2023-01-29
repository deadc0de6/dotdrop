#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6

# stop on first error
set -e

rl="readlink -f"
if ! ${rl} "${0}" >/dev/null 2>&1; then
  rl="realpath"

  if ! hash ${rl}; then
    echo "\"${rl}\" not found!" && exit 1
  fi
fi
cur=$(dirname "$(${rl} "${0}")")

tmpworkdir="/tmp/dotdrop-tests-workdir"
export DOTDROP_WORKDIR="${tmpworkdir}"

# check if tmp dir is present
workdir_tmp_exists="no"
[ -d "${HOME}/.config/dotdrop/tmp" ] && workdir_tmp_exists="yes"

# run bash tests
if [ -z "${GITHUB_WORKFLOW}" ]; then
  ## local
  tests-ng/tests_launcher.py
else
  ## CI/CD
  # running multiple jobs in parallel sometimes
  # messes with the results on remote servers
  tests-ng/tests_launcher.py 1
fi

# clear workdir
[ "${workdir_tmp_exists}" = "no" ] && rm -rf ~/.config/dotdrop/tmp
# clear temp workdir
rm -rf "${tmpworkdir}"