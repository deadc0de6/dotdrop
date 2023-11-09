#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test dynamic actions
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
variables:
  var1: "var1"
  var2: "{{@@ var1 @@}} var2"
  var3: "{{@@ var2 @@}} var3"
  var4: "{{@@ dvar4 @@}}"
dynvariables:
  dvar1: "echo dvar1"
  dvar2: "{{@@ dvar1 @@}} dvar2"
  dvar3: "{{@@ dvar2 @@}} dvar3"
  dvar4: "echo {{@@ var3 @@}}"
actions:
  pre:
    preaction1: "echo {{@@ var3 @@}} > ${tmpa}/preaction1"
    preaction2: "echo {{@@ dvar3 @@}} > ${tmpa}/preaction2"
  post:
    postaction1: "echo {{@@ var3 @@}} > ${tmpa}/postaction1"
    postaction2: "echo {{@@ dvar3 @@}} > ${tmpa}/postaction2"
  naked1: "echo {{@@ var3 @@}} > ${tmpa}/naked1"
  naked2: "echo {{@@ dvar3 @@}} > ${tmpa}/naked2"
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    actions:
      - preaction1
      - preaction2
      - postaction1
      - postaction2
      - naked1
      - naked2
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo "test" > "${tmps}"/dotfiles/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 --verbose

# checks
[ ! -e "${tmpa}"/preaction1 ] && exit 1
[ ! -e "${tmpa}"/preaction2 ] && exit 1
[ ! -e "${tmpa}"/postaction1 ] && exit 1
[ ! -e "${tmpa}"/postaction2 ] && exit 1
[ ! -e "${tmpa}"/naked1 ] && exit 1
[ ! -e "${tmpa}"/naked2 ] && exit 1

grep 'var1 var2 var3' "${tmpa}"/preaction1 >/dev/null
grep 'dvar1 dvar2 dvar3' "${tmpa}"/preaction2 >/dev/null
grep 'var1 var2 var3' "${tmpa}"/postaction1 >/dev/null
grep 'dvar1 dvar2 dvar3' "${tmpa}"/postaction2 >/dev/null
grep 'var1 var2 var3' "${tmpa}"/naked1 >/dev/null
grep 'dvar1 dvar2 dvar3' "${tmpa}"/naked2 >/dev/null

echo "OK"
exit 0
