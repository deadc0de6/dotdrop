#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test actions per profile
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

# the dotfile source
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
#echo "dotfile destination: ${tmpd}"
# the action temp
tmpa=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpa}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
actions:
  pre:
    preaction: echo 'pre' >> ${tmpa}/pre
    preaction2: echo 'pre2' >> ${tmpa}/pre2
  post:
    postaction: echo 'post' >> ${tmpa}/post
    postaction2: echo 'post2' >> ${tmpa}/post2
  nakedaction: echo 'naked' >> ${tmpa}/naked
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
  f_def:
    dst: ${tmpd}/def
    src: def
  f_ghi:
    dst: ${tmpd}/ghi
    src: ghi
profiles:
  p0:
    actions:
    - preaction2
    - postaction2
    - nakedaction
    dotfiles:
    - f_abc
    - f_def
    - f_ghi
_EOF
#cat ${cfg}

# list profiles
cd "${ddpath}" | ${bin} profiles -c "${cfg}" -V

# create the dotfile
echo "test" > "${tmps}"/dotfiles/abc
echo "test" > "${tmps}"/dotfiles/def
echo "test" > "${tmps}"/dotfiles/ghi

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p0 -V

# check actions executed
[ ! -e "${tmpa}"/pre2 ] && echo 'action not executed' && exit 1
[ ! -e "${tmpa}"/post2 ] && echo 'action not executed' && exit 1
[ ! -e "${tmpa}"/naked ] && echo 'action not executed' && exit 1

grep pre2 "${tmpa}"/pre2
nb=$(wc -l "${tmpa}"/pre2 | awk '{print $1}')
[ "${nb}" != "1" ] && echo "profile action executed multiple times" && exit 1

grep post2 "${tmpa}"/post2
nb=$(wc -l "${tmpa}"/post2 | awk '{print $1}')
[ "${nb}" != "1" ] && echo "profile action executed multiple times" && exit 1

grep naked "${tmpa}"/naked
nb=$(wc -l "${tmpa}"/naked | awk '{print $1}')
[ "${nb}" != "1" ] && echo "profile action executed multiple times" && exit 1

# install again
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p0 -V

# check actions not executed twice
nb=$(wc -l "${tmpa}"/post2 | awk '{print $1}')
[ "${nb}" -gt "1" ] && echo "action post2 executed twice" && exit 1
nb=$(wc -l "${tmpa}"/naked | awk '{print $1}')
[ "${nb}" -gt "1" ] && echo "action naked executed twice" && exit 1

echo "OK"
exit 0
