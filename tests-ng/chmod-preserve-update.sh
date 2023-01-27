#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6
#
# test chmod preserve on update
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
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

##
# existing files
##

# file
echo "exists-original" > "${tmps}"/dotfiles/exists
chmod 644 "${tmps}"/dotfiles/exists
echo "exists" > "${tmpd}"/exists
chmod 700 "${tmpd}"/exists

# link
echo "existslink" > "${tmps}"/dotfiles/existslink
chmod 700 "${tmps}"/dotfiles/existslink
ln -s "${tmps}"/dotfiles/existslink "${tmpd}"/existslink

# directory
mkdir -p "${tmps}"/dotfiles/direxists
echo "f1-original" > "${tmps}"/dotfiles/direxists/f1
mkdir -p "${tmpd}"/direxists
echo "f1" > "${tmpd}"/direxists/f1
chmod 700 "${tmpd}"/direxists/f1
chmod 700 "${tmpd}"/direxists

# link children
mkdir -p "${tmps}"/dotfiles/linkchildren
echo "f1-original" > "${tmps}"/dotfiles/linkchildren/f1
chmod 700 "${tmps}"/dotfiles/linkchildren/f1
mkdir -p "${tmps}"/dotfiles/linkchildren/d1
chmod 700 "${tmps}"/dotfiles/linkchildren/d1
echo "f2-original" > "${tmps}"/dotfiles/linkchildren/d1/f2
chmod 700 "${tmps}"/dotfiles/linkchildren/d1/f2

mkdir -p "${tmpd}"/linkchildren
chmod 700 "${tmpd}"/linkchildren
echo "f1" > "${tmpd}"/linkchildren/f1
mkdir -p "${tmpd}"/linkchildren/d1
echo "f2" > "${tmpd}"/linkchildren/d1/f2

# no mode
echo 'nomode-original' > "${tmps}"/dotfiles/nomode
echo 'nomode' > "${tmpd}"/nomode

# create the config file
cfg="${tmps}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  force_chmod: true
dotfiles:
  f_exists:
    src: exists
    dst: ${tmpd}/exists
    chmod: preserve
  f_existslink:
    src: existslink
    dst: ${tmpd}/existslink
    chmod: preserve
    link: absolute
  d_direxists:
    src: direxists
    dst: ${tmpd}/direxists
    chmod: preserve
  d_linkchildren:
    src: linkchildren
    dst: ${tmpd}/linkchildren
    chmod: preserve
    link: link_children
  f_nomode:
    src: nomode
    dst: ${tmpd}/nomode
    chmod: preserve
profiles:
  p1:
    dotfiles:
    - f_exists
    - f_existslink
    - d_direxists
    - d_linkchildren
    - f_nomode
_EOF
#cat ${cfg}

echo "update"
cd "${ddpath}" | ${bin} update -f -c "${cfg}" -p p1 -V "${tmpd}"/exists
cd "${ddpath}" | ${bin} update -f -c "${cfg}" -p p1 -V "${tmpd}"/existslink
cd "${ddpath}" | ${bin} update -f -c "${cfg}" -p p1 -V "${tmpd}"/direxists
cd "${ddpath}" | ${bin} update -f -c "${cfg}" -p p1 -V "${tmpd}"/linkchildren
cd "${ddpath}" | ${bin} update -f -c "${cfg}" -p p1 -V "${tmpd}"/nomode

count=$(cat "${cfg}" | grep chmod | grep -v 'chmod: preserve\|force_chmod' | wc -l)
echo "${count}"
[ "${count}" != "0" ] && echo "chmod altered" && exit 1

echo "OK"
exit 0
