#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# the only purpose is to test corner-cases
# not covered by other tests like
# dry
# diff before write
# etc
#
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

clear_on_exit "${basedir}"

export DOTDROP_WORKERS=1

# create the config file
cfg="${basedir}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_x:
    src: /tmp/x
    dst:
  f_y:
    src: /tmp/.i-do-not-exist-dotdrop
    dst: /tmp/y
profiles:
  p1:
    dotfiles:
    - f_x
    - f_y

_EOF

echo "[+] test install dry"
cd "${ddpath}" | ${bin} install -c "${cfg}" --dry -p p1 --verbose f_x
[ "$?" != "0" ] && exit 1

echo "[+] test install show-diff"
cd "${ddpath}" | ${bin} install -c "${cfg}" -p p1 --verbose f_x
[ "$?" != "0" ] && exit 1
cd "${ddpath}" | ${bin} install -D -c "${cfg}" -p p1 --verbose f_x
[ "$?" != "0" ] && exit 1

echo "[+] test install not existing src"
cd "${ddpath}" | ${bin} install -c "${cfg}" -f --dry -p p1 --verbose f_y

echo "[+] test install to temp"
cd "${ddpath}" | ${bin} install -t -c "${cfg}" -p p1 --verbose f_x > "${basedir}"/log 2>&1
[ "$?" != "0" ] && echo "install to tmp failed" && exit 1

# cleaning
tmpfile=$(cat "${basedir}"/log | grep 'installed to tmp ' | sed 's/^.*to tmp "\(.*\)"./\1/')
echo "tmpfile: ${tmpfile}"
rm -rf "${tmpfile}"

echo "OK"
exit 0
