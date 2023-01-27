#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6
#
# test toml config
# returns 1 in case of error
#

# exit on first error
set -e

# all this crap to get current path
rl="readlink -f"
if ! ${rl} "${0}" >/dev/null 2>&1; then
  rl="realpath"

  if ! hash ${rl}; then
    echo "\"${rl}\" not found !" && exit 1
  fi
fi
cur=$(dirname "$(${rl} "${0}")")

#hash dotdrop >/dev/null 2>&1
#[ "$?" != "0" ] && echo "install dotdrop to run tests" && exit 1

#echo "called with ${1}"

# dotdrop path can be pass as argument
ddpath="${cur}/../"
[ "${1}" != "" ] && ddpath="${1}"
[ ! -d "${ddpath}" ] && echo "ddpath \"${ddpath}\" is not a directory" && exit 1

export PYTHONPATH="${ddpath}:${PYTHONPATH}"
bin="python3 -m dotdrop.dotdrop"
if hash coverage 2>/dev/null; then
  bin="coverage run -a --source=dotdrop -m dotdrop.dotdrop"
fi

echo "dotdrop path: ${ddpath}"
echo "pythonpath: ${PYTHONPATH}"

# get the helpers
# shellcheck source=tests-ng/helpers
source "${cur}"/helpers

echo -e "$(tput setaf 6)==> RUNNING $(basename "${BASH_SOURCE[0]}") <==$(tput sgr0)"

################################################################
# this is the test
################################################################

# the dotfile source
tmp=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
tmpf="${tmp}/dotfiles"
mkdir -p "${tmpf}"
echo "dotfiles source (dotpath): ${tmpf}"

# create the config file
cfg="${tmp}/config.toml"
echo "config file: ${cfg}"

# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
echo "dotfiles destination: ${tmpd}"

clear_on_exit "${tmp}"
clear_on_exit "${tmpd}"

## RELATIVE
cat > "${cfg}" << _EOF
[config]
backup = true
create = true
dotpath = "dotfiles"

[dotfiles.f_abc]
dst = "${tmpd}/abc"
src = "abc"
link = true

[profiles.p1]
dotfiles = [ "f_abc",]
_EOF
#cat ${cfg}

# create the dotfile
echo "{{@@ profile @@}}" > "${tmpf}"/abc
echo "{{@@ profile @@}}" > "${tmpd}"/def

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b -V
[ ! -e "${tmpd}"/abc ] && echo "[ERROR] dotfile not installed" && exit 1

# import
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -b -V "${tmpd}"/def
[ ! -e "${tmpf}""${tmpd}"/def ] && echo "[ERROR] dotfile not imported" && exit 1

# checks
cnt=$(cd "${ddpath}" | ${bin} files -G -c "${cfg}" -p p1 -V | grep '^f_' | wc -l)
[ "${cnt}" != "2" ] && echo "[ERROR]" && exit 1

## CLEANING
rm -rf "${tmp}" "${tmpd}"

echo "OK"
exit 0
