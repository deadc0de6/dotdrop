#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test migration from link/link_children to single entry
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
  backup: false
  create: true
  dotpath: dotfiles
  link_by_default: true
dotfiles:
  f_link:
    dst: ${tmpd}/abc
    src: abc
    link: true
  f_link1:
    dst: ${tmpd}/abc
    src: abc
    link: true
  f_nolink:
    dst: ${tmpd}/abc
    src: abc
    link: false
  f_nolink1:
    dst: ${tmpd}/abc
    src: abc
    link: false
  f_children:
    dst: ${tmpd}/abc
    src: abc
    link_children: true
  f_children2:
    dst: ${tmpd}/abc
    src: abc
    link_children: true
  f_children3:
    dst: ${tmpd}/abc
    src: abc
    link_children: false
profiles:
  p1:
    dotfiles:
    - f_link
    - f_nolink
    - f_nolink1
    - f_children
    - f_children2
    - f_children3
_EOF
cat "${cfg}"

# create the dotfiles
echo "test" > "${tmps}"/dotfiles/abc
echo "test" > "${tmpd}"/abc

# compare
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1
# install
#cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

cat "${cfg}"

# fail if find some of these entries
echo "========> test for bad entries"
set +e
grep 'link_children: true' "${cfg}" >/dev/null && exit 1
grep 'link_children: false' "${cfg}" >/dev/null && exit 1
grep 'link: true' "${cfg}" >/dev/null && exit 1
grep 'link: false' "${cfg}" >/dev/null && exit 1
grep 'link_by_default: true' "${cfg}" >/dev/null && exit 1
grep 'link_by_default: false' "${cfg}" >/dev/null && exit 1
set -e

# test values have been correctly updated
echo "========> test for updated entries"
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -G | grep '^f_link' | head -1 | grep ',link:absolute,'
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -G | grep '^f_nolink'    | head -1 | grep ',link:nolink,'
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -G | grep '^f_nolink1'   | head -1 | grep ',link:nolink,'
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -G | grep '^f_children'  | head -1 | grep ',link:link_children,'
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -G | grep '^f_children2' | head -1 | grep ',link:link_children,'
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -G | grep '^f_children3' | head -1 | grep ',link:nolink,'

echo "OK"
exit 0
