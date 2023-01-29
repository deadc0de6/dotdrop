#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2021, deadc0de6
#
# import config testing
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
  bin="coverage run -p --source=dotdrop -m dotdrop.dotdrop"
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

# the dotfile sources
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

first="${tmps}/first"
second="${tmps}/second"
mkdir -p "${first}" "${second}"

# create the config file
cfg1="${first}/config.yaml"
cfg2="${second}/config.yaml"

cat > "${cfg1}" << _EOF
config:
  backup: true
  create: true
  dotpath: .
  import_configs:
  - ../second/config.yaml
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p0:
    include:
    - p1
    dotfiles:
    - f_abc
_EOF

cat > "${cfg2}" << _EOF
config:
  backup: true
  create: true
  dotpath: .
dotfiles:
  f_def:
    dst: ${tmpd}/def
    src: def
profiles:
  p1:
    dotfiles:
    - f_def
_EOF

# create the source
echo "abc" > "${first}"/abc
echo "{{@@ _dotfile_abs_dst @@}}" >> "${first}"/abc

echo "def" > "${second}"/def
echo "{{@@ _dotfile_abs_dst @@}}" >> "${second}"/def

# files comparison
cd "${ddpath}" | ${bin} files -c "${cfg1}" -G -p p0 | grep '^f_abc'
cd "${ddpath}" | ${bin} files -c "${cfg1}" -G -p p0 | grep '^f_def'
cd "${ddpath}" | ${bin} files -c "${cfg1}" -G -p p1 | grep '^f_def'
cd "${ddpath}" | ${bin} files -c "${cfg2}" -G -p p1 | grep '^f_def'

# test compare too
cd "${ddpath}" | ${bin} install -c "${cfg1}" -p p0 -V -f
cd "${ddpath}" | ${bin} compare -c "${cfg1}" -p p0 -V

[ ! -s "${tmpd}"/abc ] && echo "abc not installed" && exit 1
[ ! -s "${tmpd}"/def ] && echo "def not installed" && exit 1

echo "OK"
exit 0
