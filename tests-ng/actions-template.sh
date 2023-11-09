#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test action template execution
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
    preaction: "echo {{@@ _dotfile_abs_src @@}} > {0}"
  post:
    postaction: "echo {{@@ _dotfile_abs_src @@}} > ${tmpa}/post"
  nakedaction: "echo {{@@ _dotfile_abs_src @@}} > ${tmpa}/naked"
config:
  backup: true
  create: true
  dotpath: dotfiles
  default_actions:
  - preaction "${tmpa}/pre"
  - postaction
  - nakedaction
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo 'test' > "${tmps}"/dotfiles/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

# checks action
[ ! -e "${tmpa}"/pre ] && echo 'pre action not executed' && exit 1
[ ! -e "${tmpa}"/post ] && echo 'post action not executed' && exit 1
[ ! -e "${tmpa}"/naked ] && echo 'naked action not executed'  && exit 1
grep abc "${tmpa}"/pre >/dev/null
grep abc "${tmpa}"/post >/dev/null
grep abc "${tmpa}"/naked >/dev/null

# clear
rm -f "${tmpa}"/naked* "${tmpa}"/pre* "${tmpa}"/post* "${tmpd}"/abc

cat > "${cfg}" << _EOF
actions:
  pre:
    preaction: "echo {{@@ _dotfile_abs_dst @@}} > ${tmpa}/pre"
  post:
    postaction: "echo {{@@ _dotfile_abs_dst @@}} > ${tmpa}/post"
  nakedaction: "echo {{@@ _dotfile_abs_dst @@}} > ${tmpa}/naked"
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
      - nakedaction
      - postaction
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

# checks action
[ ! -e "${tmpa}"/pre ] && echo 'pre action not executed' && exit 1
[ ! -e "${tmpa}"/post ] && echo 'post action not executed' && exit 1
[ ! -e "${tmpa}"/naked ] && echo 'naked action not executed'  && exit 1
grep "${tmpd}/abc" "${tmpa}"/pre >/dev/null
grep "${tmpd}/abc" "${tmpa}"/post >/dev/null
grep "${tmpd}/abc" "${tmpa}"/naked >/dev/null

echo "OK"
exit 0
