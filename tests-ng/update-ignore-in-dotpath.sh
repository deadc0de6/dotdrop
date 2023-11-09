#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6
#
# test ignore update in dotpath
# returns 1 in case of error
#

## start-cookie
set -eu -o errtrace -o pipefail
cur=$(cd "$(dirname "${0}")" && pwd)
ddpath="${cur}/../"
PPATH="{PYTHONPATH:-}"
export PYTHONPATH="${ddpath}:${PPATH}"
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
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
# fs dotfiles
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
dt="${tmps}/dotfiles"
mkdir -p "${dt}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create to-be-imported files
mkdir -p "${tmpd}"/test
echo 'original' > "${tmpd}"/test/config1
mkdir -p "${tmpd}"/test/ignoreme
echo 'original' > "${tmpd}"/test/ignoreme/config2

# create the config file
cfg="${tmps}/config.yaml"
create_conf "${cfg}" # sets token

# import
echo "[+] import"
cd "${ddpath}" | ${bin} import -c "${cfg}" -f --verbose --profile=p1 "${tmpd}"/test

# remove ignoreme
echo "[+] remove ignoreme"
rm -r "${tmpd}"/test/ignoreme

# update
echo "[+] update"
cd "${ddpath}" | ${bin} update -f -c "${cfg}" --verbose --profile=p1 --key d_test

# check files haven't been updated
[ -d "${dt}"/"${tmpd}"/test/ignoreme ] && echo "ignoreme should have been removed" && exit 1

echo "OK"
exit 0
