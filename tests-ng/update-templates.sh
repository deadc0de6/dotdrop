#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test update of templates
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
echo "dotfiles source (dotpath): ${tmps}"
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
echo "dotfiles destination: ${tmpd}"
# the workdir
tmpw=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
export DOTDROP_WORKDIR="${tmpw}"
echo "workdir: ${tmpw}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpw}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  workdir: ${tmpw}
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
echo "head" > "${tmps}"/dotfiles/abc
echo '{%@@ if profile == "p1" @@%}' >> "${tmps}"/dotfiles/abc
echo "is p1" >> "${tmps}"/dotfiles/abc
echo '{%@@ else @@%}' >> "${tmps}"/dotfiles/abc
echo "is not p1" >> "${tmps}"/dotfiles/abc
echo '{%@@ endif @@%}' >> "${tmps}"/dotfiles/abc
echo "tail" >> "${tmps}"/dotfiles/abc

# create the installed dotfile
echo "head" > "${tmpd}"/abc
echo "is p1" >> "${tmpd}"/abc
echo "tail" >> "${tmpd}"/abc

# update
#cat ${tmps}/dotfiles/abc
set +e
patch=$(cd "${ddpath}" | ${bin} update -P -p p1 -k f_abc --cfg "${cfg}" 2>&1 | grep 'try patching with' | sed 's/"//g')
set -e
# shellcheck disable=SC2001
patch=$(echo "${patch}" | sed 's/^.*: //g')
echo "patching with: ${patch}"
eval "${patch}"
#cat ${tmps}/dotfiles/abc

echo "OK"
exit 0
