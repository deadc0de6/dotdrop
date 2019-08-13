#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

# check for readlink/realpath presence
# https://github.com/deadc0de6/dotdrop/issues/6
rl="readlink -f"

if ! ${rl} "${0}" >/dev/null 2>&1; then
  rl="realpath"

  if ! hash ${rl}; then
    echo "\"${rl}\" not found!" && exit 1
  fi
fi

# setup variables
args=("$@")
cur=$(dirname "$(${rl} "${0}")")
opwd=$(pwd)
cfg="${cur}/config.yaml"
sub="dotdrop"

# pivot
cd "${cur}" || { echo "Directory \"${cur}\" doesn't exist, aborting." && exit 1; }
# init/update the submodule
if [ "${DOTDROP_AUTOUPDATE-yes}" = yes ] ; then
  git submodule update --init --recursive
  git submodule update --remote dotdrop
fi
# launch dotdrop
PYTHONPATH=dotdrop python3 -m dotdrop.dotdrop "${args[@]}"
ret="$?"
# pivot back
cd "${opwd}" || { echo "Directory \"${opwd}\" doesn't exist, aborting." && exit 1; }
# exit with dotdrop exit code
exit ${ret}
