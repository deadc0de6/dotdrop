#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test remove
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
mkdir -p "${tmps}"/dotfiles
# the dotfile to be imported
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
  f_def:
    dst: ${tmpd}/def
    src: def
  f_last:
    dst: ${tmpd}/last
    src: last
profiles:
  p1:
    dotfiles:
    - f_abc
    - f_def
  p2:
    dotfiles:
    - f_def
  last:
    dotfiles:
    - f_last
_EOF
cfgbak="${tmps}/config.yaml.bak"
cp "${cfg}" "${cfgbak}"

# create the dotfile
echo "abc" > "${tmps}"/dotfiles/abc
echo "abc" > "${tmpd}"/abc

echo "def" > "${tmps}"/dotfiles/def
echo "def" > "${tmpd}"/def

# remove with bad profile
cd "${ddpath}" | ${bin} remove -f -k -p empty -c "${cfg}" f_abc -V
[ ! -e "${tmps}"/dotfiles/abc ] && echo "dotfile in dotpath deleted" && exit 1
[ ! -e "${tmpd}"/abc ] && echo "source dotfile deleted" && exit 1
[ ! -e "${tmps}"/dotfiles/def ] && echo "dotfile in dotpath deleted" && exit 1
[ ! -e "${tmpd}"/def ] && echo "source dotfile deleted" && exit 1
# ensure config not altered
diff "${cfg}" "${cfgbak}"

# remove by key
echo "[+] remove f_abc by key"
cd "${ddpath}" | ${bin} remove -p p1 -f -k -c "${cfg}" f_abc -V
cat "${cfg}"
echo "[+] remove f_def by key"
cd "${ddpath}" | ${bin} remove -p p2 -f -k -c "${cfg}" f_def -V
cat "${cfg}"

# checks
[ -e "${tmps}"/dotfiles/abc ] && echo "dotfile in dotpath not deleted" && exit 1
[ ! -e "${tmpd}"/abc ] && echo "source dotfile deleted" && exit 1

[ -e "${tmps}"/dotfiles/def ] && echo "dotfile in dotpath not deleted" && exit 1
[ ! -e "${tmpd}"/def ] && echo "source dotfile deleted" && exit 1

echo "[+] ========="

# create the config file
cfg="${tmps}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
  f_def:
    dst: ${tmpd}/def
    src: def
  f_last:
    dst: ${tmpd}/last
    src: last
profiles:
  p1:
    dotfiles:
    - f_abc
    - f_def
  p2:
    dotfiles:
    - f_def
  last:
    dotfiles:
    - f_last
_EOF
cat "${cfg}"

# create the dotfile
echo "abc" > "${tmps}"/dotfiles/abc
echo "abc" > "${tmpd}"/abc

echo "def" > "${tmps}"/dotfiles/def
echo "def" > "${tmpd}"/def

# remove by key
echo "[+] remove f_abc by path"
cd "${ddpath}" | ${bin} remove -p p1 -f -c "${cfg}" "${tmpd}"/abc -V
cat "${cfg}"
echo "[+] remove f_def by path"
cd "${ddpath}" | ${bin} remove -p p2 -f -c "${cfg}" "${tmpd}"/def -V
cat "${cfg}"

# checks
[ -e "${tmps}"/dotfiles/abc ] && echo "(2) dotfile in dotpath not deleted" && exit 1
[ ! -e "${tmpd}"/abc ] && echo "(2) source dotfile deleted" && exit 1

[ -e "${tmps}"/dotfiles/def ] && echo "(2) dotfile in dotpath not deleted" && exit 1
[ ! -e "${tmpd}"/def ] && echo "(2) source dotfile deleted" && exit 1


cat "${cfg}"

echo "OK"
exit 0
