#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test cmpignore
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
mkdir -p "${tmpd}"/{program,config}
touch "${tmpd}"/program/a
touch "${tmpd}"/config/a

# create the config file
cfg="${basedir}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF

# import
echo "[+] import"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/program
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/config

# add files
echo "[+] add files"
touch "${tmpd}"/program/b
touch "${tmpd}"/config/b

# adding ignore in dotfile
cfg2="${basedir}/config2.yaml"
sed '/dotpath: dotfiles/a \ \ cmpignore:\n\ \ \ \ - "*/config/b"' "${cfg}" > "${cfg2}"
cat "${cfg2}"

# expects one diff
echo "[+] comparing with ignore in dotfile - 1 diff"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg2}" --verbose
[ "$?" = "0" ] && exit 1
set -e

# adding ignore in dotfile
cfg2="${basedir}/config2.yaml"
sed '/dotpath: dotfiles/a \ \ cmpignore:\n\ \ \ \ - "*b"' "${cfg}" > "${cfg2}"
cat "${cfg2}"

# expects no diff
echo "[+] comparing with ignore in dotfile - 0 diff"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg2}" --verbose
[ "$?" != "0" ] && exit 1
set -e

echo "OK"
exit 0
