#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6
#
# test bad diff cmd
# returns 1 in case of error
#

## start-cookie
set -e
cur=$(cd "$(dirname "${0}")" && pwd)
ddpath="${cur}/../"
export PYTHONPATH="${ddpath}:${PYTHONPATH}"
altbin="python3 -m dotdrop.dotdrop"
if hash coverage 2>/dev/null; then
  altbin="coverage run -p --source=dotdrop -m dotdrop.dotdrop"
fi
bin="${DT_BIN:-${altbin}}"
# shellcheck source=tests-ng/helpers
source "${cur}"/helpers
echo -e "$(tput setaf 6)==> RUNNING $(basename "${BASH_SOURCE[0]}") <==$(tput sgr0)"
## end-cookie

################################################################
# this is the test
################################################################
basedir=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
echo "[+] dotdrop dir: ${basedir}"

clear_on_exit "${basedir}"

# create the config file
cfg="${basedir}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  diff_command: xxxxxxxxx {0} {1}
dotfiles:
profiles:
_EOF

set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}"
[ "$?" = "0" ] && exit 1

out=$(cd "${ddpath}" | ${bin} compare -c "${cfg}")
echo "${out}" | grep -i 'traceback' && exit 1

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  diff_command:
dotfiles:
profiles:
_EOF

set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}"
[ "$?" = "0" ] && exit 1

out=$(cd "${ddpath}" | ${bin} compare -c "${cfg}")
echo "${out}" | grep -i 'traceback' && exit 1

echo "OK"
exit 0
