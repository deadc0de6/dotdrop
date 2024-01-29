#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test updates and rights
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

# the dotfile directory to be imported
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
# the dotfile file to be imported
tmpf=$(mktemp)

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

# single file
echo 'file' > "${tmpf}"

mkdir "${tmpd}"/dir1
echo 'dir1file1' > "${tmpd}"/dir1/file1
echo 'dir1file2' > "${tmpd}"/dir1/file2

# create the config file
cfg="${basedir}/config.yaml"
create_conf "${cfg}" # sets token

# import dir1
echo "[+] import"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpf}"

# change file
chmod +x "${tmpf}"

# update
echo "[+] updating (1)"
cd "${ddpath}" | ${bin} update -c "${cfg}" -f --verbose "${tmpf}"

# test change applied
[ "$(stat -c '%a' "${tmpf}")" != "$(stat -c '%a' "${basedir}"/dotfiles/"${tmpf}")" ] && exit 1

# change file
chmod +x "${tmpd}"/dir1/file2
echo 'test' > "${tmpd}"/dir1/newfile
chmod +x "${tmpd}"/dir1/newfile

# update
echo "[+] updating (2)"
cd "${ddpath}" | ${bin} update -c "${cfg}" -f --verbose "${tmpd}"

# test change applied
stat1=$(stat -c '%a' "${tmpd}"/dir1/newfile)
stat2=$(stat -c '%a' "${basedir}"/dotfiles/"${tmpd}"/dir1/newfile)
[ "${stat1}" != "${stat2}" ] && echo "diff permissions for newfile: ${stat1} VS ${stat2}" && exit 1
stat1=$(stat -c '%a' "${tmpd}"/dir1/file2)
stat2=$(stat -c '%a' "${basedir}"/dotfiles/"${tmpd}"/dir1/file2)
[ "${stat1}" != "${stat2}" ] && echo "diff permissions for file2: ${stat1} VS ${stat2}" && exit 1

echo "OK"
exit 0
