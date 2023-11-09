#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test minversion

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
    link: true
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# create the source
mkdir -p "${tmps}"/dotfiles/
echo "abc" > "${tmps}"/dotfiles/abc
ln -s "${tmps}"/dotfiles/abc "${tmpd}"/abc

# compare
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1 -V

# ensure minversion is present
cat "${cfg}"
grep 'link: absolute' "${cfg}"
grep 'minversion' "${cfg}"

# fake a higher version
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  minversion: 100.1.2
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    link: true
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# compare
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1 -V
[ "$?" != "1" ] && echo "minversion not working" && exit 1
set -e

# all clean
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
  p1:
    dotfiles:
    - f_abc
_EOF

# compare
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1 -V

# test
cat "${cfg}"
grep 'minversion' "${cfg}" && echo "minversion added, not needed" && exit 1

echo "OK"
exit 0
