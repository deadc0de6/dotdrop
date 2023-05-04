#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test ignore update
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

# $1 pattern
# $2 path
grep_or_fail()
{
  grep "${1}" "${2}" >/dev/null 2>&1 || (echo "pattern \"${1}\" not found in ${2}" && exit 1)
}

# dotdrop directory
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
# fs dotfiles
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
dt="${tmps}/dotfiles"
mkdir -p "${dt}"

# dotfiles in dotdrop
mkdir -p "${dt}"/a/{b,c,x}
echo 'a' > "${dt}"/a/b/abfile
echo 'a' > "${dt}"/a/c/acfile
echo 'a' > "${dt}"/a/x/xfile

cp -r "${dt}"/a "${tmpd}"/

mkdir -p "${dt}"/a/be-gone
echo 'a' > "${dt}"/a/be-gone/file

# filesystem files
touch "${tmpd}"/a/newfile
echo 'b' > "${tmpd}"/a/c/acfile
mkdir -p "${tmpd}"/a/newdir/b
touch "${tmpd}"/a/newdir/b/c
mkdir -p "${tmpd}"/a/x
echo "b" > "${tmpd}"/a/x/xfile

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
  f_abc:
    dst: ${tmpd}/a
    src: a
    upignore:
    - "*/cfile"
    - "*/newfile"
    - "*/newdir"
    - "*/x/**"
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# update
echo "[+] update"
cd "${ddpath}" | ${bin} update -f -c "${cfg}" --verbose --profile=p1 --key f_abc

# check files haven't been updated
grep_or_fail 'b' "${dt}/a/c/acfile"
grep_or_fail 'a' "${dt}/a/x/xfile"
[ -e "${dt}"/a/newfile ] && echo "should not have been updated" && exit 1
[ -d "${dt}"/a/be-gone ] && echo "should have been removed" && exit 1

echo "OK"
exit 0
