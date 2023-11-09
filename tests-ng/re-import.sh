#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test re-importing file
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

# the dotfile source
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${HOME}/.dotdrop-test"

# create the dotfile
echo "original" > "${tmpd}"/testfile

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

# import
echo "[+] import file"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V "${tmpd}"/testfile
cat "${cfg}"

# ensure exists and is not link
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/testfile ] && echo "does not exist" && exit 1
cat "${cfg}" | grep "${tmpd}"/testfile >/dev/null 2>&1
grep 'original' "${tmps}"/dotfiles/"${tmpd}"/testfile
nb=$(cat "${cfg}" | grep "${tmpd}"/testfile | wc -l)
[ "${nb}" != "1" ] && echo 'not 1 entry' && exit 1

# re-import without changing
echo "[+] re-import without changes"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V "${tmpd}"/testfile
cat "${cfg}"

# test is only once
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/testfile ] && echo "does not exist" && exit 1
cat "${cfg}" | grep "${tmpd}"/testfile >/dev/null 2>&1
grep 'original' "${tmps}"/dotfiles/"${tmpd}"/testfile
nb=$(cat "${cfg}" | grep "${tmpd}"/testfile | wc -l)
[ "${nb}" != "1" ] && echo 'two entries!' && exit 1

# re-import with changes
echo "[+] re-import with changes"
echo 'modified' > "${tmpd}"/testfile
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V "${tmpd}"/testfile
cat "${cfg}"

# test is only once
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/testfile ] && echo "does not exist" && exit 1
cat "${cfg}" | grep "${tmpd}"/testfile >/dev/null 2>&1
grep 'modified' "${tmps}"/dotfiles/"${tmpd}"/testfile
nb=$(cat "${cfg}" | grep "${tmpd}"/testfile | wc -l)
[ "${nb}" != "1" ] && echo 'two entries!' && exit 1

# ###################################################

echo 'original' > "${HOME}/.dotdrop.test"
# import in home
echo "[+] import file in home"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V ~/.dotdrop.test
cat "${cfg}"

# ensure exists and is not link
[ ! -e "${tmps}/dotfiles/dotdrop.test" ] && echo "does not exist" && exit 1
# shellcheck disable=SC2088
cat "${cfg}" | grep '~/.dotdrop.test'
grep 'original' "${tmps}"/dotfiles/dotdrop.test
# shellcheck disable=SC2088
nb=$(cat "${cfg}" | grep '~/.dotdrop.test' | wc -l)
[ "${nb}" != "1" ] && echo 'not 1 entry' && exit 1

# re-import without changing
echo "[+] re-import without changes in home"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V ~/.dotdrop.test
cat "${cfg}"

# test is only once
[ ! -e "${tmps}/dotfiles/dotdrop.test" ] && echo "does not exist" && exit 1
# shellcheck disable=SC2088
cat "${cfg}" | grep '~/.dotdrop.test' >/dev/null 2>&1
grep 'original' "${tmps}"/dotfiles/dotdrop.test
# shellcheck disable=SC2088
nb=$(cat "${cfg}" | grep '~/.dotdrop.test' | wc -l)
[ "${nb}" != "1" ] && echo 'two entries!' && exit 1

# re-import with changes
echo "[+] re-import with changes in home"
echo 'modified' > ~/.dotdrop.test
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V ~/.dotdrop.test
cat "${cfg}"

# test is only once
[ ! -e "${tmps}/dotfiles/dotdrop.test" ] && echo "does not exist" && exit 1
# shellcheck disable=SC2088
cat "${cfg}" | grep '~/.dotdrop.test' >/dev/null 2>&1
grep 'modified' "${tmps}"/dotfiles/dotdrop.test
# shellcheck disable=SC2088
nb=$(cat "${cfg}" | grep '~/.dotdrop.test' | wc -l)
[ "${nb}" != "1" ] && echo 'two entries!' && exit 1

echo "OK"
exit 0
