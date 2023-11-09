#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test recursive include
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
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
  f_def:
    dst: ${tmpd}/def
    src: def
profiles:
  host:
    include:
    - user
  common:
    dotfiles:
    - f_def
  user:
    dotfiles:
    - f_abc
    include:
    - common
_EOF

# create the source
mkdir -p "${tmps}"/dotfiles/
content_abc="testrecinclude_abc"
echo "${content_abc}" > "${tmps}"/dotfiles/abc
content_def="testrecinclude_def"
echo "${content_def}" > "${tmps}"/dotfiles/def

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p host -V

# checks
[ ! -e "${tmpd}"/abc ] && echo "abc not installed" && exit 1
echo "abc installed"
grep ${content_abc} "${tmpd}"/abc

[ ! -e "${tmpd}"/def ] && echo "def not installed" && exit 1
echo "def installed"
grep ${content_def} "${tmpd}"/def

# test cyclic include
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
  f_def:
    dst: ${tmpd}/def
    src: def
profiles:
  host:
    include:
    - user
  common:
    include:
    - host
    dotfiles:
    - f_def
  user:
    dotfiles:
    - f_abc
    include:
    - common
_EOF

# install
set +e
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p host -V
[ "$?" = 0 ] && exit 1
set -e

echo "OK"
exit 0
