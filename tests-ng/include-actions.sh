#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test the use of the keyword "include"
# with action inheritance
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
# the action temp
tmpa=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpa}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
actions:
  pre:
    preaction: echo 'pre' >> ${tmpa}/pre
    preaction2: echo 'pre2' >> ${tmpa}/pre2
  post:
    postaction: echo 'post' >> ${tmpa}/post
    postaction2: echo 'post2' >> ${tmpa}/post2
  nakedaction: echo 'naked' >> ${tmpa}/naked
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
    - p3
  p1:
    dotfiles:
    - f_abc
    actions:
    - preaction
    - postaction
  p2:
    include:
    - p1
    actions:
    - preaction2
    - postaction2
  p3:
    include:
    - p2
    actions:
    - nakedaction
_EOF

# create the source
mkdir -p "${tmps}"/dotfiles/
echo "test" > "${tmps}"/dotfiles/abc

# install
echo "PROFILE p2"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p2 -V

# checks
[ ! -e "${tmpa}"/pre ] && echo "pre not found" && exit 1
nb=$(wc -l "${tmpa}"/pre | awk '{print $1}')
[ "${nb}" != "1" ] && echo "pre executed multiple times" && exit 1

[ ! -e "${tmpa}"/pre2 ] && echo "pre2 not found" && exit 1
nb=$(wc -l "${tmpa}"/pre2 | awk '{print $1}')
[ "${nb}" != "1" ] && echo "pre2 executed multiple times" && exit 1

[ ! -e "${tmpa}"/post ] && echo "post not found" && exit 1
nb=$(wc -l "${tmpa}"/post | awk '{print $1}')
[ "${nb}" != "1" ] && echo "post executed multiple times" && exit 1

[ ! -e "${tmpa}"/post2 ] && echo "post2 not found" && exit 1
nb=$(wc -l "${tmpa}"/post2 | awk '{print $1}')
[ "${nb}" != "1" ] && echo "post2 executed multiple times" && exit 1

# install
rm -f "${tmpa}"/pre "${tmpa}"/pre2 "${tmpa}"/post "${tmpa}"/post2 "${tmpa}"/naked
rm -f "${tmpd}"/abc
echo "PROFILE p3"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p3 -V

# checks
[ ! -e "${tmpa}"/pre ] && echo "pre not found" && exit 1
nb=$(wc -l "${tmpa}"/pre | awk '{print $1}')
[ "${nb}" != "1" ] && echo "pre executed multiple times" && exit 1

[ ! -e "${tmpa}"/pre2 ] && echo "pre2 not found" && exit 1
nb=$(wc -l "${tmpa}"/pre2 | awk '{print $1}')
[ "${nb}" != "1" ] && echo "pre2 executed multiple times" && exit 1

[ ! -e "${tmpa}"/post ] && echo "post not found" && exit 1
nb=$(wc -l "${tmpa}"/post | awk '{print $1}')
[ "${nb}" != "1" ] && echo "post executed multiple times" && exit 1

[ ! -e "${tmpa}"/post2 ] && echo "post2 not found" && exit 1
nb=$(wc -l "${tmpa}"/post2 | awk '{print $1}')
[ "${nb}" != "1" ] && echo "post2 executed multiple times" && exit 1

[ ! -e "${tmpa}"/naked ] && echo "naked not found" && exit 1
nb=$(wc -l "${tmpa}"/naked | awk '{print $1}')
[ "${nb}" != "1" ] && echo "naked executed multiple times" &&  exit 1

# install
rm -f "${tmpa}"/pre "${tmpa}"/pre2 "${tmpa}"/post "${tmpa}"/post2 "${tmpa}"/naked
rm -f "${tmpd}"/abc
echo "PROFILE p0"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p0 -V

# checks
[ ! -e "${tmpa}"/pre ] && echo "pre not found" && exit 1
nb=$(wc -l "${tmpa}"/pre | awk '{print $1}')
[ "${nb}" != "1" ] && echo "pre executed multiple times" && exit 1

[ ! -e "${tmpa}"/pre2 ] && echo "pre2 not found" && exit 1
nb=$(wc -l "${tmpa}"/pre2 | awk '{print $1}')
[ "${nb}" != "1" ] && echo "pre2 executed multiple times" && exit 1

[ ! -e "${tmpa}"/post ] && echo "post not found" && exit 1
nb=$(wc -l "${tmpa}"/post | awk '{print $1}')
[ "${nb}" != "1" ] && echo "post executed multiple times" && exit 1

[ ! -e "${tmpa}"/post2 ] && echo "post2 not found" && exit 1
nb=$(wc -l "${tmpa}"/post2 | awk '{print $1}')
[ "${nb}" != "1" ] && echo "post2 executed multiple times" && exit 1

[ ! -e "${tmpa}"/naked ] && echo "naked not found" && exit 1
nb=$(wc -l "${tmpa}"/naked | awk '{print $1}')
[ "${nb}" != "1" ] && echo "naked executed multiple times" &&  exit 1

# install without verbose
rm -f "${tmpa}"/pre "${tmpa}"/pre2 "${tmpa}"/post "${tmpa}"/post2 "${tmpa}"/naked
rm -f "${tmpd}"/abc
echo "PROFILE p0 without verbose"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p0

# checks
[ ! -e "${tmpa}"/pre ] && echo "pre not found" && exit 1
nb=$(wc -l "${tmpa}"/pre | awk '{print $1}')
[ "${nb}" != "1" ] && echo "pre executed multiple times" && exit 1

[ ! -e "${tmpa}"/pre2 ] && echo "pre2 not found" && exit 1
nb=$(wc -l "${tmpa}"/pre2 | awk '{print $1}')
[ "${nb}" != "1" ] && echo "pre2 executed multiple times" && exit 1

[ ! -e "${tmpa}"/post ] && echo "post not found" && exit 1
nb=$(wc -l "${tmpa}"/post | awk '{print $1}')
[ "${nb}" != "1" ] && echo "post executed multiple times" && exit 1

[ ! -e "${tmpa}"/post2 ] && echo "post2 not found" && exit 1
nb=$(wc -l "${tmpa}"/post2 | awk '{print $1}')
[ "${nb}" != "1" ] && echo "post2 executed multiple times" && exit 1

[ ! -e "${tmpa}"/naked ] && echo "naked not found" && exit 1
nb=$(wc -l "${tmpa}"/naked | awk '{print $1}')
[ "${nb}" != "1" ] && echo "naked executed multiple times" &&  exit 1

echo "OK"
exit 0
