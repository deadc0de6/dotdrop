#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# force actions
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

# the action temp
tmpa=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
# the dotfile source
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpa}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
actions:
  pre:
    preaction: echo 'pre' > ${tmpa}/pre
    preaction2: echo 'pre2' > ${tmpa}/pre2
  post:
    postaction: echo 'post' > ${tmpa}/post
    postaction2: echo 'post2' > ${tmpa}/post2
  nakedaction: echo 'naked' > ${tmpa}/naked
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    actions:
      - preaction
      - postaction
      - nakedaction
      - preaction2
      - postaction2
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo "test" > "${tmps}"/dotfiles/abc
# deploy the dotfile
cp "${tmps}"/dotfiles/abc "${tmpd}"/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

# checks
[ -e "${tmpa}"/pre ] && exit 1
[ -e "${tmpa}"/post ] && exit 1
[ -e "${tmpa}"/naked ] && exit 1
[ -e "${tmpa}"/pre2 ] && exit 1
[ -e "${tmpa}"/post2 ] && exit 1

# install and force
cd "${ddpath}" | ${bin} install -f -a -c "${cfg}" -p p1 -V

# checks
[ ! -e "${tmpa}"/pre ] && exit 1
grep pre "${tmpa}"/pre >/dev/null
[ ! -e "${tmpa}"/post ] && exit 1
grep post "${tmpa}"/post >/dev/null
[ ! -e "${tmpa}"/naked ] && exit 1
grep naked "${tmpa}"/naked >/dev/null
[ ! -e "${tmpa}"/pre2 ] && exit 1
grep pre2 "${tmpa}"/pre2 >/dev/null
[ ! -e "${tmpa}"/post2 ] && exit 1
grep post2 "${tmpa}"/post2 >/dev/null

echo "OK"
exit 0
