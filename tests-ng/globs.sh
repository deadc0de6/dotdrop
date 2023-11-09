#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# ensure imports allow globs
# - import_actions
# - import_configs
# - import_variables
# - profile import
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
# temporary
tmpa=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpa}"

###########
# test globs in import_actions
###########
# create the action files
actionsd="${tmps}/actions"
mkdir -p "${actionsd}"
cat > "${actionsd}"/action1.yaml << _EOF
actions:
  fromaction1: echo "fromaction1" > ${tmpa}/fromaction1
_EOF
cat > "${actionsd}"/action2.yaml << _EOF
actions:
  fromaction2: echo "fromaction2" > ${tmpa}/fromaction2
_EOF

cfg="${tmps}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_actions:
  - ${actionsd}/*
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    actions:
      - fromaction1
      - fromaction2
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# create the source
mkdir -p "${tmps}"/dotfiles/
echo "abc" > "${tmps}"/dotfiles/abc

# install
cd "${ddpath}" | ${bin} install -c "${cfg}" -f -p p1 -V

# checks
[ ! -e "${tmpd}"/abc ] && echo "dotfile not installed" && exit 1
[ ! -e  "${tmpa}"/fromaction1 ] && echo "action1 not executed" && exit 1
grep fromaction1 "${tmpa}"/fromaction1
[ ! -e  "${tmpa}"/fromaction2 ] && echo "action2 not executed" && exit 1
grep fromaction2 "${tmpa}"/fromaction2

echo "OK"
exit 0
