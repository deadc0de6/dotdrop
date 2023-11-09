#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6
#
# test chmod dir sub file on install
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
  [ "${mode}" != "$2" ] && echo "bad mode for $(basename "$1") (${mode} VS expected ${2})" && exit 1
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

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  force_chmod: true
dotfiles:
  d_dir:
    src: dir
    dst: ${tmpd}/dir
profiles:
  p1:
    dotfiles:
    - d_dir
_EOF
#cat ${cfg}

mkdir -p "${tmps}"/dotfiles/dir
echo 'file1' > "${tmps}"/dotfiles/dir/file1
chmod 700 "${tmps}"/dotfiles/dir/file1
echo 'file2' > "${tmps}"/dotfiles/dir/file2
chmod 777 "${tmps}"/dotfiles/dir/file2
echo 'file3' > "${tmps}"/dotfiles/dir/file3
chmod 644 "${tmps}"/dotfiles/dir/file3

ls -l "${tmps}"/dotfiles/dir/

# install
echo "install (1)"
cd "${ddpath}" | ${bin} install -c "${cfg}" -f -p p1 -V

has_rights "${tmpd}/dir/file1" "700"
has_rights "${tmpd}/dir/file2" "777"
has_rights "${tmpd}/dir/file3" "644"

# modify
chmod 666 "${tmpd}/dir/file1"
chmod 666 "${tmpd}/dir/file2"
chmod 666 "${tmpd}/dir/file3"

# install
echo "install (2)"
cd "${ddpath}" | ${bin} install -c "${cfg}" -f -p p1 -V

has_rights "${tmpd}/dir/file1" "700"
has_rights "${tmpd}/dir/file2" "777"
has_rights "${tmpd}/dir/file3" "644"

echo "OK"
exit 0
