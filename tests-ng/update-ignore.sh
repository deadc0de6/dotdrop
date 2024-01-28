#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test ignore update
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
  grep "${1}" "${2}" >/dev/null 2>&1 || (echo "pattern \"${1}\" not found in ${2}" && exit 1)
}

# dotdrop directory
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
# fs dotfiles
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
dt="${tmps}/dotfiles"
mkdir -p "${dt}"
clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# "a" dotfiles in dotdrop
mkdir -p "${dt}"/a/{b,c,x}
echo 'a' > "${dt}"/a/b/abfile
echo 'a' > "${dt}"/a/c/acfile
echo 'a' > "${dt}"/a/x/xfile

# "dir" dotfiles in dotdrop
mkdir -p "${dt}"/dir/{a,b,c}
echo 'a' > "${dt}"/dir/a/a
echo 'b' > "${dt}"/dir/b/b
echo 'c' > "${dt}"/dir/c/c

# create destinations
cp -r "${dt}"/a "${tmpd}"/
cp -r "${dt}"/dir "${tmpd}"/

# update "a" dotdrop files
mkdir -p "${dt}"/a/be-gone
echo 'a' > "${dt}"/a/be-gone/file

# update "a" filesystem files
touch "${tmpd}"/a/newfile
echo 'b' > "${tmpd}"/a/c/acfile
mkdir -p "${tmpd}"/a/newdir/b
touch "${tmpd}"/a/newdir/b/c
mkdir -p "${tmpd}"/a/x
echo "b" > "${tmpd}"/a/x/xfile
echo "c" > "${tmpd}"/a/x/yfile

# update "dir" filesystem
echo "new" > "${tmpd}"/dir/a/a
touch "${dt}"/dir/a/be-gone
touch "${tmpd}"/dir/newfile
mkdir -p "${tmpd}"/dir/ignore
echo "ignore-me" > "${tmpd}"/dir/ignore/ignore-me
echo 'ignore-me' > "${tmpd}"/dir/ignore-file

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
    - "*/x/*"
  d_dir:
    dst: ${tmpd}/dir
    src: dir
    upignore:
    - "*/ignore/*"
    - "*/ignore-file"
profiles:
  p1:
    dotfiles:
    - f_abc
    - d_dir
_EOF

# update
echo "[+] update"
cd "${ddpath}" | ${bin} update -f --verbose -c "${cfg}" --profile=p1

# check "a" files are correct
grep_or_fail 'b' "${dt}/a/c/acfile"
grep_or_fail 'a' "${dt}/a/x/xfile"
[ -e "${dt}"/a/newfile ] && echo "'a' newfile should have been removed" && exit 1
[ -e "${dt}"/a/be-gone ] && echo "'file' be-gone should have been removed" && exit 1
[ -e "${dt}"/x/yfile ] && echo "'a' yfile should not have been added" && exit 1

# check "dir" files are correct
grep_or_fail 'new' "${dt}"/dir/a/a
[ -e "${dt}"/dir/a/be-gone ] && echo "'file' be-gone should have been removed" && exit 1
[ ! -e "${tmpd}"/dir/newfile ] && echo "'dir' newfile should have been removed" && exit 1
[ -d "${dt}"/dir/ignore ] && echo "'dir' ignore dir not ignored" && exit 1
[ -f "${dt}"/dir/ignore/ignore-me ] && echo "'dir' ignore-me not ignored" && exit 1
[ -f "${dt}"/dir/ignore-file ] && echo "'dir' ignore-file not ignored" && exit 1

echo "OK"
exit 0
