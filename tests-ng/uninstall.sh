#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6
#
# test uninstall (no symlink)
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
export DOTDROP_TEST_NG_UNINSTALL_DDPATH="${ddpath}"
export DOTDROP_TEST_NG_UNINSTALL_BIN="${bin}"
source "${cur}"/uninstall_

export DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE="nolink"
echo "[+] testing uninstall link:${DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE}..."
uninstall_with_link
echo "[+] uninstall link ${DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE} OK"

export DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE="absolute"
echo "[+] testing uninstall link:${DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE}..."
uninstall_with_link
echo "[+] uninstall link ${DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE} OK"

export DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE="relative"
echo "[+] testing uninstall link:${DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE}..."
uninstall_with_link
echo "[+] uninstall link ${DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE} OK"

export DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE="link_children"
echo "[+] testing uninstall link:${DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE}..."
uninstall_with_link
echo "[+] uninstall link ${DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE} OK"

# TODO test
# - symlink file (absolute, relative)
# - symlink directory (absolute, relative, link_children)
# - transformation
# - template

echo "OK"
exit 0