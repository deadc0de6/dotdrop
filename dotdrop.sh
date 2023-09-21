#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

ENV_DIR=${DOTDROP_VIRTUALENV:-}

# setup variables
args=("$@")
cur=$(cd "$(dirname "${0}")" && pwd)
opwd=$(pwd)

# pivot
cd "${cur}" || { echo "Directory \"${cur}\" doesn't exist, aborting." && exit 1; }

# init/update the submodule
if [ "${DOTDROP_AUTOUPDATE-yes}" = yes ] ; then
  git submodule update --init --recursive
  git submodule update --remote dotdrop
fi

# check python executable
pybin="python3"
if [ -z "${ENV_DIR}" ]; then
  hash ${pybin} 2>/dev/null || pybin="python"
  [[ "$(${pybin} -V 2>&1)" =~ "Python 3" ]] || { echo "install Python 3" && exit 1; }
else
  # virtualenv
  pybin="${ENV_DIR}/bin/python"
fi
hash "${pybin}" 2>/dev/null || { echo "python executable not found" && exit 1; }

# launch dotdrop
PYTHONPATH=dotdrop:${PYTHONPATH} ${pybin} -m dotdrop.dotdrop "${args[@]}"
ret="$?"

# pivot back
cd "${opwd}" || { echo "Directory \"${opwd}\" doesn't exist, aborting." && exit 1; }

# exit with dotdrop exit code
exit ${ret}
