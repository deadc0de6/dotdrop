#!/usr/bin/env bash
# author: deadc0de6
#
# test negative ignore on compare
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

# filesystem
mkdir -p "${tmpd}"/a/{b,c,d,x}
echo "updated" > "${tmpd}/a/b/abfile1"
echo "updated" > "${tmpd}/a/b/abfile2"
echo "updated" > "${tmpd}/a/b/abfile3"
echo "updated" > "${tmpd}/a/c/acfile"
echo "updated" > "${tmpd}/a/d/adfile"
echo "updated" > "${tmpd}/a/x/axfile"

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
    cmpignore:
    - "*"
    - "!*/c/**"
    - "!*/d/**"
    - "!x/**"
profiles:
  p1:
    dotfiles:
    - d_abc
_EOF

# compare
echo "[+] compare"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" --verbose --profile=p1
ret="$?"
echo "return code: ${ret}"
[ "${ret}" != "1" ] && exit 1
set -e

echo "OK"
exit 0
