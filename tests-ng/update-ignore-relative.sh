#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test ignore update relative pattern
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
    - "cfile"
    - "newfile"
    - "newdir"
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

#tree ${tmpd}/a

# update
echo "[+] update"
cd "${ddpath}" | ${bin} update -f -c "${cfg}" --verbose --profile=p1 --key f_abc

#tree ${dt}

# check files haven't been updated
grep 'b' "${dt}"/a/c/acfile >/dev/null || (echo "b not found" && exit 1)
[ -e "${dt}"/a/newfile ] && echo "new file does not exist" && exit 1

echo "OK"
exit 0
