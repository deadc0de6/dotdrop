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
  grep "${1}" "${2}" >/dev/null 2>&1 || (echo "pattern not found in ${2}" && exit 1)
}

# dotdrop directory
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
dt="${tmps}/dotfiles"
mkdir -p "${dt}"
mkdir -p "${dt}"/a/{b,c}
echo 'a' > "${dt}"/a/b/abfile
echo 'a' > "${dt}"/a/c/acfile

# fs dotfiles
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

cp -r "${dt}"/a "${tmpd}"/

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
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

#tree ${dt}

# edit/add files
echo "[+] edit/add files"
touch "${tmpd}"/a/newfile
echo 'b' > "${tmpd}"/a/c/acfile
mkdir -p "${tmpd}"/a/newdir/b
touch "${tmpd}"/a/newdir/b/c

# update
echo "[+] update"
cd "${ddpath}" | ${bin} update -f -c "${cfg}" --verbose --profile=p1 --key f_abc

# check files haven't been updated
grep_or_fail 'b' "${dt}/a/c/acfile"
[ -e "${dt}"/a/newfile ] && echo "should not have been updated" && exit 1

echo "OK"
exit 0
