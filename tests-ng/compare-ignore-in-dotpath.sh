#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6
#
# test compare ignore (see #405)
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
basedir=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"

# the dotfile to be imported
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

# some files
mkdir -p "${tmpd}"/test
echo 'original' > "${tmpd}"/test/config1
mkdir -p "${tmpd}"/test/ignoreme
echo 'original' > "${tmpd}"/test/ignoreme/config2

# create the config file
cfg="${basedir}/config.yaml"
create_conf "${cfg}" # sets token

# import
echo "[+] import"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/test

# remove ignoreme
echo "[+] remove ignoreme in dotpath"
rm -r "${basedir}"/dotfiles/"${tmpd}"/test/ignoreme

# expects diff
echo "[+] comparing normal - diff expected"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" --verbose
[ "$?" = "0" ] && exit 1
set -e

# expects zero diff diff
patt="ignoreme"
echo "[+] comparing with ignore (pattern: ${patt}) - no diff expected"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" --verbose --ignore="${patt}"
[ "$?" != "0" ] && exit 1
set -e

echo "OK"
exit 0
