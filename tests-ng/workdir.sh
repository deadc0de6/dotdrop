#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test workdir relative or absolute
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
unset DOTDROP_WORKDIR
string="blabla"

# the dotfile source
tmp=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

tmpf="${tmp}/dotfiles"
tmpw="${tmp}/workdir"
export DOTDROP_WORKDIR="${tmpw}"

mkdir -p "${tmpf}"
echo "dotfiles source (dotpath): ${tmpf}"
mkdir -p "${tmpw}"
echo "workdir: ${tmpw}"

# create the config file
cfg="${tmp}/config.yaml"
echo "config file: ${cfg}"

# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
echo "dotfiles destination: ${tmpd}"

clear_on_exit "${tmp}"
clear_on_exit "${tmpd}"

## RELATIVE
echo "RUNNING RELATIVE"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  workdir: $(echo "${tmpw}" | sed 's/^.*\///g')
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    link: true
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo "{{@@ profile @@}}" > "${tmpf}"/abc
echo "${string}" >> "${tmpf}"/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b -V

# checks
grep -r p1 "${tmpw}" >/dev/null
grep -r ${string} "${tmpw}" >/dev/null
[ ! -e "${tmpd}"/abc ] && echo "[ERROR] dotfile not installed" && exit 1
[ ! -h "${tmpd}"/abc ] && echo "[ERROR] dotfile is not a symlink" && exit 1

## CLEANING
rm -rf "${tmp}" "${tmpd}"

## ABSOLUTE
echo "RUNNING ABSOLUTE"
# the dotfile source
tmp=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

tmpf="${tmp}/dotfiles"
tmpw="${tmp}/workdir"
export DOTDROP_WORKDIR="${tmpw}"

mkdir -p "${tmpf}"
echo "dotfiles source (dotpath): ${tmpf}"
mkdir -p "${tmpw}"
echo "workdir: ${tmpw}"

# create the config file
cfg="${tmp}/config.yaml"
echo "config file: ${cfg}"

# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
echo "dotfiles destination: ${tmpd}"

clear_on_exit "${tmp}"
clear_on_exit "${tmpd}"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  workdir: ${tmpw}
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    link: true
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo "{{@@ profile @@}}" > "${tmpf}"/abc
echo "${string}" >> "${tmpf}"/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b -V

# checks
grep -r p1 "${tmpw}" >/dev/null
grep -r ${string} "${tmpw}" >/dev/null
[ ! -e "${tmpd}"/abc ] && echo "[ERROR] dotfile not installed" && exit 1
[ ! -h "${tmpd}"/abc ] && echo "[ERROR] dotfile is not a symlink" && exit 1

## CLEANING
rm -rf "${tmp}" "${tmpd}"

## NONE
echo "RUNNING UNDEFINED WORKDIR"
# the dotfile source
tmp=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

tmpf="${tmp}/dotfiles"

mkdir -p "${tmpf}"
echo "dotfiles source (dotpath): ${tmpf}"

# create the config file
cfg="${tmp}/config.yaml"
echo "config file: ${cfg}"

# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
echo "dotfiles destination: ${tmpd}"

clear_on_exit "${tmp}"
clear_on_exit "${tmpd}"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    link: true
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo "{{@@ profile @@}}" > "${tmpf}"/abc
echo "${string}" >> "${tmpf}"/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b -V

# checks
#grep -r p1 ${tmpw} >/dev/null
#grep -r ${string} ${tmpw} >/dev/null
[ ! -e "${tmpd}"/abc ] && echo "[ERROR] dotfile not installed" && exit 1
[ ! -h "${tmpd}"/abc ] && echo "[ERROR] dotfile is not a symlink" && exit 1

echo "OK"
exit 0
