#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test the use of the keyword "include"
# and (dyn)variables precedence
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
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
# the dotfile destination
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
variables:
  var: nopv
dynvariables:
  dvar: "echo nopdv"
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p0:
    variables:
      var: p0v
    dynvariables:
      dvar: "echo p0dv"
    include:
    - p1
  p1:
    dotfiles:
    - f_abc
    variables:
      var: p1v
    dynvariables:
      dvar: "echo p1dv"
_EOF
#cat ${cfg}

# create the source
mkdir -p "${tmps}"/dotfiles/
echo "head" > "${tmps}"/dotfiles/abc
echo "{{@@ var @@}}" >> "${tmps}"/dotfiles/abc
echo "{{@@ dvar @@}}" >> "${tmps}"/dotfiles/abc
echo "tail" >> "${tmps}"/dotfiles/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p0 --verbose

#cat ${tmpd}/abc
grep 'p0v' "${tmpd}"/abc
grep 'p0dv' "${tmpd}"/abc

echo "OK"
exit 0
