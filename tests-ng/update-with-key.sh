#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test updates with key
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

# originally imported directory
echo 'unique' > "${tmpd}"/uniquefile
uniquefile_key="f_uniquefile"
echo 'unique2' > "${tmpd}"/uniquefile2
mkdir "${tmpd}"/dir1
touch "${tmpd}"/dir1/dir1f1
mkdir "${tmpd}"/dir1/dir1dir1

# create the config file
cfg="${basedir}/config.yaml"
create_conf "${cfg}" # sets token

# import dir1
echo "[+] import"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/dir1
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/uniquefile
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/uniquefile2

# make some modification
echo "[+] modify"
echo 'changed' > "${tmpd}"/uniquefile
echo 'changed' > "${tmpd}"/uniquefile2
echo 'new' > "${tmpd}"/dir1/dir1dir1/new

# update by key
echo "[+] updating single key"
cd "${ddpath}" | ${bin} update -c "${cfg}" -k -f --verbose ${uniquefile_key}

# ensure changes applied correctly (only to uniquefile)
diff "${tmpd}"/uniquefile "${basedir}"/dotfiles/"${tmpd}"/uniquefile # should be same
set +e
diff "${tmpd}"/uniquefile2 "${basedir}"/dotfiles/"${tmpd}"/uniquefile2 # should be different
[ "${?}" != "1" ] && exit 1
set -e

# update all keys
echo "[+] updating all keys"
cd "${ddpath}" | ${bin} update -c "${cfg}" -k -f --verbose

# ensure all changes applied
diff "${tmpd}" "${basedir}"/dotfiles/"${tmpd}"

echo "OK"
exit 0
