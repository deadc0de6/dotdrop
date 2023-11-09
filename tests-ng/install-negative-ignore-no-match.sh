#!/usr/bin/env bash
# author: jtt9340 (https://github.com/jtt9340)
# author: deadc0de6
#
# test that dotdrop warns when a negative ignore pattern
# does not match a file that would be ignored
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
basedir=$(mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d)
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"

# the dotfile to be imported
tmpd=$(mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d)

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

# some files
mkdir -p "${tmpd}"/program/ignore_me
echo "some data" > "${tmpd}"/program/a
echo "some data" > "${tmpd}"/program/ignore_me/b
echo "some data" > "${tmpd}"/program/ignore_me/c

# create the config file
cfg="${basedir}/config.yaml"
create_conf "${cfg}" # sets token

# import
echo "[+] import"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/program

# adding ignore in dotfile
cfg2="${basedir}/config2.yaml"
sed '/d_program:/a\
\ \ \ \ instignore:\
\ \ \ \ - "!*/ignore_me/c"
' "${cfg}" > "${cfg2}"

# install
rm -rf "${tmpd}"
echo "[+] install with negative ignore in dotfile"
echo '(1) expect dotdrop install to warn when negative ignore pattern does not match an already-ignored file'

patt="[WARN] no files that are currently being ignored match \"*/ignore_me/c\". In order for a negative ignore
pattern to work, it must match a file that is being ignored by a previous ignore pattern."
cd "${ddpath}" | ${bin} install -c "${cfg2}" --verbose 2>&1 >/dev/null | grep -F "${patt}" ||
  (echo "dotdrop did not warn when negative ignore pattern did not match an already-ignored file" && exit 1)

echo "OK"
exit 0
