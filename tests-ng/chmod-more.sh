#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2020, deadc0de6
#
# test chmod on import
# with files and directories
# with different link
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

# $1 path
# $2 rights
has_rights()
{
  echo "testing ${1} is ${2}"
  [ ! -e "$1" ] && echo "$(basename "$1") does not exist" && exit 1
  local mode
  mode=$(stat -L -c '%a' "$1")
  [ "${mode}" != "$2" ] && echo "bad mode for $(basename "$1") (${mode} instead of ${2})" && exit 1
  true
}

# the dotfile source
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the dotfiles
f1="${tmpd}/f1"
touch "${f1}"
chmod 777 "${f1}"
stat -c '%a' "${f1}"

f2="${tmpd}/f2"
touch "${f2}"
chmod 644 "${f2}"
stat -c '%a' "${f2}"

toimport="${f1} ${f2}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF
#cat ${cfg}

# import without --preserve-mode
for i in ${toimport}; do
  stat -c '%a' "${i}"
  cd "${ddpath}" | ${bin} import -c "${cfg}" -f -p p1 -V "${i}"
done

cat "${cfg}"

has_rights "${tmpd}/f1" "777"
has_rights "${tmps}/dotfiles/${tmpd}/f1" "777"
has_rights "${tmpd}/f2" "644"
has_rights "${tmps}/dotfiles/${tmpd}/f2" "644"

# install
cd "${ddpath}" | ${bin} install -c "${cfg}" -f -p p1 -V | grep '0 dotfile(s) installed' || (echo "should not install" && exit 1)

echo "OK"
exit 0
