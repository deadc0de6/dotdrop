#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test external actions
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

act="${tmps}/actions.yaml"
cat > "${act}" << _EOF
actions:
  pre:
    preaction: echo 'pre' > ${tmpa}/pre
  post:
    postaction: echo 'post' > ${tmpa}/post
  nakedaction: echo 'naked' > ${tmpa}/naked
  overwrite: echo 'over' > ${tmpa}/write
_EOF

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_actions:
  - ${tmps}/actions.yaml
actions:
  overwrite: echo 'write' > ${tmpa}/write
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    actions:
      - preaction
      - postaction
      - nakedaction
      - overwrite
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo "test" > "${tmps}"/dotfiles/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

# checks
[ ! -e "${tmpa}"/pre ] && exit 1
grep pre "${tmpa}"/pre >/dev/null
echo "pre is ok"

[ ! -e "${tmpa}"/post ] && exit 1
grep post "${tmpa}"/post >/dev/null
echo "post is ok"

[ ! -e "${tmpa}"/naked ] && exit 1
grep naked "${tmpa}"/naked >/dev/null
echo "naked is ok"

[ ! -e "${tmpa}"/write ] && exit 1
grep over "${tmpa}"/write >/dev/null
echo "write is ok"

echo "OK"
exit 0
