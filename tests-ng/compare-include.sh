#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6
#
# test compare in profile which includes another
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

# create the dotfiles already imported
echo "already in" > "${tmps}"/dotfiles/abc
cp "${tmps}"/dotfiles/abc "${tmpd}"/abc

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
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
    dotfiles:
    include:
    - p1
    - p2
  p1:
    dotfiles:
    variables:
      somevar: somevalue
  p2:
    dotfiles:
    - f_abc
_EOF
cat "${cfg}"

cd "${ddpath}" | ${bin} files -c "${cfg}" -p p0

cnt=$(cd "${ddpath}" | ${bin} files -c "${cfg}" -p p0 | grep '^f_' | wc -l)
[ "${cnt}" != "1" ] && echo "this is bad" && exit 1

# compare
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p0

echo "modifying"
echo 'modified' > "${tmpd}"/abc

# compare
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p0
ret=$?
[ "${ret}" = "0" ] && echo "compare should fail (returned ${ret})" && exit 1
set -e

# count
cnt=$(cd "${ddpath}" | ${bin} files -c "${cfg}" -p p0 -b | grep '^f_' | wc -l)
[ "${cnt}" != "2" ] && echo "not enough dotfile" exit 1

## without dotfiles: entry
# reset dotfile content
echo "already in" > "${tmps}"/dotfiles/abc
cp "${tmps}"/dotfiles/abc "${tmpd}"/abc

cat > "${cfg}" << _EOF
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
    - p1
    - p2
  p1:
    variables:
      somevar: somevalue
  p2:
    dotfiles:
    - f_abc
_EOF
cat "${cfg}"

cd "${ddpath}" | ${bin} files -c "${cfg}" -p p0

cnt=$(cd "${ddpath}" | ${bin} files -c "${cfg}" -p p0 | grep '^f_' | wc -l)
[ "${cnt}" != "1" ] && echo "this is bad" && exit 1

# compare
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p0

echo "modifying"
echo 'modified' > "${tmpd}"/abc

# compare
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p0
ret=$?
[ "${ret}" = "0" ] && echo "compare should fail (returned ${ret})" && exit 1
set -e

# count
cnt=$(cd "${ddpath}" | ${bin} files -c "${cfg}" -p p0 -b | grep '^f_' | wc -l)
[ "${cnt}" != "2" ] && echo "not enough dotfile" exit 1

echo "OK"
exit 0
