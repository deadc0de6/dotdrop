#!/usr/bin/env bash
# author: deadc0de6
#
# test negative ignore on install
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
  [ ! -e "${2}" ] && (echo "file ${2} does not exist" && exit 1)
  grep "${1}" "${2}" >/dev/null 2>&1 || (echo "pattern \"${1}\" not found in ${2}" && exit 1)
}

# dotdrop directory
basedir=$(mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d)
# the dotfile to be updated
tmpd=$(mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d)

echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"
echo "[+] dst dir: ${tmpd}"

# dotfiles in dotdrop
mkdir -p "${basedir}"/dotfiles/a/{b,c,x}
echo 'original' > "${basedir}"/dotfiles/a/b/abfile1
echo 'original' > "${basedir}"/dotfiles/a/b/abfile2
echo 'original' > "${basedir}"/dotfiles/a/b/abfile3
echo 'original' > "${basedir}"/dotfiles/a/c/acfile
echo 'original' > "${basedir}"/dotfiles/a/x/axfile

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${basedir}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: false
  create: true
  dotpath: dotfiles
dotfiles:
  d_abc:
    dst: ${tmpd}/a
    src: a
    instignore:
    - "*"
    - "!*/c/**"
    - "!*/d/**"
    - "!x/**"
profiles:
  p1:
    dotfiles:
    - d_abc
_EOF

# install
echo "[+] install"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" --verbose --profile=p1

[ -d "${tmpd}/a/b" ] && (echo "/a/b created" && exit 1)
grep_or_fail "original" "${tmpd}/a/c/acfile"
#grep_or_fail "original" "${tmpd}/a/d/adfile"
grep_or_fail "original" "${tmpd}/a/x/axfile"

echo "OK"
exit 0
