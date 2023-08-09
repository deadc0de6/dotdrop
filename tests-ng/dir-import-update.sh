#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test importing and updating entire directories
# returns 1 in case of error
#

## start-cookie
set -e
cur=$(cd "$(dirname "${0}")" && pwd)
ddpath="${cur}/../"
export PYTHONPATH="${ddpath}:${PYTHONPATH}"
altbin="python3 -m dotdrop.dotdrop"
if hash coverage 2>/dev/null; then
  mkdir -p coverages/
  altbin="coverage run -p --data-file coverages/coverage --source=dotdrop -m dotdrop.dotdrop"
fi
bin="${DT_BIN:-${altbin}}"
# shellcheck source=tests-ng/helpers
source "${cur}"/helpers
echo -e "$(tput setaf 6)==> RUNNING $(basename "${BASH_SOURCE[0]}") <==$(tput sgr0)"
## end-cookie

################################################################
# this is the test
################################################################

# dotdrop directory
basedir=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
echo "dotdrop dir: ${basedir}"
# the dotfile
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
create_dir "${tmpd}"

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${basedir}/config.yaml"
create_conf "${cfg}" # sets token

# import the dir
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"

# change token
echo "changed" > "${token}"

# update
cd "${ddpath}" | ${bin} update -f -c "${cfg}" "${tmpd}" --verbose

grep 'changed' "${token}" >/dev/null 2>&1

echo "OK"
exit 0
