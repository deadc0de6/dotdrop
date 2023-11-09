#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test the use of the keyword "include"
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

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
actions:
    pre:
      preaction: touch ${tmpd}/action.pre
    postaction: touch ${tmpd}/action.post
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p0:
    dotfiles:
    include:
    - p3
  p1:
    actions:
    - preaction
    - postaction
    dotfiles:
    - f_abc
  p2:
    include:
    - p1
  p3:
    include:
    - p2
_EOF
cat "${cfg}"

# create the source
mkdir -p "${tmps}"/dotfiles/
echo "test" > "${tmps}"/dotfiles/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p0 --verbose

[ ! -e "${tmpd}"/action.pre ] && exit 1
[ ! -e "${tmpd}"/action.post ] && exit 1

# compare
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p2
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p3
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p0

# list
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 | grep f_abc
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p2 | grep f_abc
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p3 | grep f_abc
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p0 | grep f_abc

cnt=$(cd "${ddpath}" | ${bin} files -c "${cfg}" -p p0 | grep f_abc | wc -l)
[ "${cnt}" != "1" ] && echo "dotfiles displayed more than once" && exit 1

# count
cnt=$(cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -b | grep '^f_' | wc -l)
[ "${cnt}" != "1" ] && exit 1

echo "OK"
exit 0
