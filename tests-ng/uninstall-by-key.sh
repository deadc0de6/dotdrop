#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2024, deadc0de6
#
# test uninstall by key
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
echo "[+] dotdrop dir: ${tmps}"
echo "[+] dotpath dir: ${tmps}/dotfiles"

# the dotfile to be imported
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"
create_conf "${cfg}" # sets token

# single file
echo 'file' > "${tmpd}"/file

# import
echo "import..."
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/file

# install
rm -f "${tmpd}"/file
echo "install..."
cd "${ddpath}" | ${bin} install -f -c "${cfg}"

# uninstall
echo "uninstall..."
cd "${ddpath}" | ${bin} uninstall -f -c "${cfg}" f_file

# nothing to uninstall
cat > "${cfg}" << _EOF
config:
  backup: false
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/file
    src: file
profiles:
  p1:
    dotfiles:
_EOF

echo "uninstall..."
cd "${ddpath}" | ${bin} uninstall -f -c "${cfg}" --profile=p1

echo "OK"
exit 0