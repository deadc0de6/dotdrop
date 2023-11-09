#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test pre/post/naked actions
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
    fake_pre: echo 'fake pre' > ${tmpa}/fake_pre
    expandvariable: "myvar=xxx; echo \${{myvar}} > ${tmpa}/expandvariable"
  post:
    postaction: echo 'post' > ${tmpa}/post
    postaction2: echo 'post2' > ${tmpa}/post2
  nakedaction: echo 'naked' > ${tmpa}/naked
  _silentaction: echo 'silent'
  fakeaction: echo 'fake' > ${tmpa}/fake
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
      - _silentaction
      - expandvariable
  f_fake:
    dst:
    src:
    actions:
      - fakeaction
      - fake_pre
profiles:
  p1:
    dotfiles:
    - f_abc
    - f_fake
_EOF
#cat ${cfg}

# create the dotfile
echo "test" > "${tmps}"/dotfiles/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V 2>&1 | tee "${tmpa}"/log

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
grep post "${tmpa}"/post2 >/dev/null
[ ! -e "${tmpa}"/log ] && exit 1
grep "executing \"echo 'naked' > ${tmpa}/naked" "${tmpa}"/log >/dev/null
grep "executing \"echo 'silent'" "${tmpa}"/log >/dev/null && false
grep "executing silent action \"_silentaction\"" "${tmpa}"/log >/dev/null
[ ! -e "${tmpa}"/expandvariable ] && exit 1
grep xxx "${tmpa}"/expandvariable >/dev/null

# fake action
[ ! -e "${tmpa}"/fake ] && echo 'fake post action not executed' && exit 1
grep fake "${tmpa}"/fake >/dev/null
[ ! -e "${tmpa}"/fake_pre ] && echo 'fake pre action not executed' && exit 1
grep 'fake pre' "${tmpa}"/fake_pre >/dev/null

echo "OK"
exit 0
