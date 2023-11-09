#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2021, deadc0de6
#
# test update dotfile from different profile
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

# $1 pattern
# $2 path
grep_or_fail()
{
  grep "${1}" "${2}" >/dev/null 2>&1 || (echo "pattern not found in ${2}" && exit 1)
}

# dotdrop directory
tmps=$(mktemp -d --suffix='-dotdrop-tests-source' || mktemp -d)
dt="${tmps}/dotfiles"
mkdir -p "${dt}"

xori="profile x"
yori="profile y"
echo "${xori}" > "${dt}"/file_x
echo "${yori}" > "${dt}"/file_y

# fs dotfiles
tmpd=$(mktemp -d --suffix='-dotdrop-tests-dest' || mktemp -d)
touch "${tmpd}"/file

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: false
  create: true
  dotpath: dotfiles
dotfiles:
  f_file_x:
    dst: ${tmpd}/file
    src: file_x
  f_file_y:
    dst: ${tmpd}/file
    src: file_y
profiles:
  x:
    dotfiles:
    - f_file_x
  y:
    dotfiles:
    - f_file_y
_EOF
cat "${cfg}"

# reset
echo "${xori}" > "${dt}"/file_x
echo "${yori}" > "${dt}"/file_y

# test with key
echo "test update x from key"
n="patched content for X"
echo "${n}" > "${tmpd}"/file
cd "${ddpath}" | ${bin} update -f -c "${cfg}" --verbose --profile=x --key f_file_x
grep_or_fail "${n}" "${dt}/file_x"
grep_or_fail "${yori}" "${dt}/file_y"

# reset
echo "${xori}" > "${dt}"/file_x
echo "${yori}" > "${dt}"/file_y

# test with key
echo "test update y from key"
n="patched content for Y"
echo "${n}" > "${tmpd}"/file
cd "${ddpath}" | ${bin} update -f -c "${cfg}" --verbose --profile=y --key f_file_y
grep_or_fail "${n}" "${dt}/file_y"
grep_or_fail "${xori}" "${dt}/file_x"

# reset
echo "${xori}" > "${dt}"/file_x
echo "${yori}" > "${dt}"/file_y

# test with path
echo "test update x from path"
n="patched content for X"
echo "${n}" > "${tmpd}"/file
cd "${ddpath}" | ${bin} update -f -c "${cfg}" --verbose --profile=x "${tmpd}/file"
grep_or_fail "${n}" "${dt}/file_x"
grep_or_fail "${yori}" "${dt}/file_y"

# reset
echo "${xori}" > "${dt}"/file_x
echo "${yori}" > "${dt}"/file_y

# test with path
echo "test update y from path"
n="patched content for Y"
echo "${n}" > "${tmpd}"/file
cd "${ddpath}" | ${bin} update -f -c "${cfg}" --verbose --profile=y "${tmpd}/file"
grep_or_fail "${n}" "${dt}/file_y"
grep_or_fail "${xori}" "${dt}/file_x"

## make sure it fails when wrong dotfile
# reset
echo "${xori}" > "${dt}"/file_x
echo "${yori}" > "${dt}"/file_y

# test with key
echo "test wrong key for x"
n="patched content for X"
echo "${n}" > "${tmpd}"/file
set +e
cd "${ddpath}" | ${bin} update -f -c "${cfg}" --verbose --profile=x --key f_file_y
set -e
grep_or_fail "${xori}" "${dt}/file_x"
grep_or_fail "${yori}" "${dt}/file_y"

# reset
echo "${xori}" > "${dt}"/file_x
echo "${yori}" > "${dt}"/file_y

# test with key
echo "test wrong key for y"
n="patched content for Y"
echo "${n}" > "${tmpd}"/file
set +e
cd "${ddpath}" | ${bin} update -f -c "${cfg}" --verbose --profile=y --key f_file_x
set -e
grep_or_fail "${xori}" "${dt}/file_x"
grep_or_fail "${yori}" "${dt}/file_y"

echo "OK"
exit 0
