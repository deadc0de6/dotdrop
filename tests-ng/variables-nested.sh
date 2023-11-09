#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6
#
# test nested variables (see #383)
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
variables:
  hello:
    k: "hello1"
  wow1: "{{@@ hello.k @@}}"
  hello2: "hello2"
  z2:
    wow2: "{{@@ hello2 @@}}"
  a:
    suba:
      subsuba: "submarine"
  b:
    subb:
      subsubb:
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
echo "wow1={{@@ wow1 @@}}" > "${tmps}"/dotfiles/abc
echo "wow2={{@@ z2.wow2 @@}}" >> "${tmps}"/dotfiles/abc
echo "subsuba={{@@ a.suba.subsuba @@}}" >> "${tmps}"/dotfiles/abc
echo "subsubb={{@@ b.subb.subsubb @@}}" >> "${tmps}"/dotfiles/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 --verbose

cat "${tmpd}"/abc

[ ! -e "${tmpd}"/abc ] && echo "abc not installed" && exit 1
grep '^wow1=hello1' "${tmpd}"/abc >/dev/null
grep '^wow2=hello2' "${tmpd}"/abc >/dev/null
grep '^subsuba=submarine' "${tmpd}"/abc >/dev/null
grep '^subsubb=None' "${tmpd}"/abc >/dev/null

echo "OK"
exit 0
