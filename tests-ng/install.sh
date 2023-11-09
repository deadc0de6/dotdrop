#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2020, deadc0de6
#
# test install
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

get_file_mode()
{
  u=$(umask)
  # shellcheck disable=SC2001
  u=$(echo "${u}" | sed 's/^0*//')
  v=$((666 - u))
  echo "${v}"
}

# $1 path
# $2 rights
has_rights()
{
  echo "testing ${1} is ${2}"
  [ ! -e "$1" ] && echo "$(basename "$1") does not exist" && exit 1
  local mode
  mode=$(stat -L -c '%a' "$1")
  [ "${mode}" != "$2" ] && echo "bad mode for $(basename "$1") (${mode} VS expected ${2})" && exit 1
  true
}

# dotdrop directory
basedir=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${basedir}"/dotfiles
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

echo "content" > "${basedir}"/dotfiles/x

# create the config file
cfg="${basedir}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_x:
    src: x
    dst: ${tmpd}/x
profiles:
  p1:
    dotfiles:
    - f_x
_EOF

echo "[+] install"
cd "${ddpath}" | ${bin} install -c "${cfg}" -f -p p1 --verbose | grep '^1 dotfile(s) installed.$'
[ "$?" != "0" ] && exit 1

[ ! -e "${tmpd}"/x ] && echo "f_x not installed" && exit 1

# update chmod
chmod 666 "${tmpd}"/x
cd "${ddpath}" | ${bin} update -c "${cfg}" -f -p p1 --verbose "${tmpd}"/x

# chmod updated
cat "${cfg}" | grep "chmod: '666'"

chmod 644 "${tmpd}"/x

mode=$(get_file_mode "${tmpd}"/x)
echo "[+] re-install with no"
(
  cd "${ddpath}"
  printf "N\n" | ${bin} install -c "${cfg}" -p p1 --verbose
  exit ${?}
)

# if user answers N, chmod should not be done
has_rights "${tmpd}/x" "${mode}"

echo "[+] re-install with yes"
(
  cd "${ddpath}"
  printf "y\n" | ${bin} install -c "${cfg}" -p p1 --verbose
  exit ${?}
)

has_rights "${tmpd}/x" "666"

echo "OK"
exit 0
