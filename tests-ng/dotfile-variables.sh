#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test dotfile specific variables
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
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo 'src:{{@@ _dotfile_abs_src @@}}' > "${tmps}"/dotfiles/abc
echo 'dst:{{@@ _dotfile_abs_dst @@}}' >> "${tmps}"/dotfiles/abc
echo 'key:{{@@ _dotfile_key @@}}' >> "${tmps}"/dotfiles/abc
echo 'link:{{@@ _dotfile_link @@}}' >> "${tmps}"/dotfiles/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

# checks
[ ! -e "${tmpd}"/abc ] && echo 'dotfile not installed' && exit 1
cat "${tmpd}"/abc
grep "src:${tmps}/dotfiles/abc" "${tmpd}"/abc >/dev/null
grep "dst:${tmpd}/abc" "${tmpd}"/abc >/dev/null
grep "key:f_abc" "${tmpd}"/abc >/dev/null
grep "link:nolink" "${tmpd}"/abc >/dev/null

echo "OK"
exit 0
