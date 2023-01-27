#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6
#
# test import in profile which includes another
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
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the dotfile to import
echo "file" > "${tmpd}"/file

# create the dotfiles already imported
echo "already in" > "${tmps}"/dotfiles/abc

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
profiles:
  p0:
    include:
    - p1
  p1:
    dotfiles:
    - f_abc
_EOF
cat "${cfg}"

cnt=$(cd "${ddpath}" | ${bin} files -c "${cfg}" -p p0 | grep '^f_' | wc -l)
[ "${cnt}" != "1" ] && echo "this is bad" && exit 1

# import
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p0 --verbose "${tmpd}"/file

[ ! -e "${tmps}"/dotfiles/"${tmpd}"/file ] && echo "file not imported" && exit 1

# make sure file is in
cnt=$(cd "${ddpath}" | ${bin} files -c "${cfg}" -p p0 | grep '^f_file' | wc -l)
[ "${cnt}" != "1" ] && echo "dotfiles not in config" && exit 1

# count
cnt=$(cd "${ddpath}" | ${bin} files -c "${cfg}" -p p0 -b | grep '^f_' | wc -l)
[ "${cnt}" != "2" ] && echo "not enough dotfile" exit 1

echo "OK"
exit 0
