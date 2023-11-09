#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test import duplicates
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
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the dotfile
touch "${tmpd}"/.colors
mkdir -p "${tmpd}"/.mutt
touch "${tmpd}"/.mutt/colors

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  longkey: false
dotfiles:
  f_colors:
    src: abc
    dst: abc
  f_mutt_colors:
    src: abc
    dst: abc
  f_$(echo "${tmpd}" | sed -e 's#^/\(.*\)$#\1#g' | sed 's#/#_#g' | tr '[:upper:]' '[:lower:]')_colors:
    src: abc
    dst: abc
  f_$(echo "${tmpd}" | sed -e 's#^/tmp/\(.*\)$#\1#g' | sed 's#/#_#g' | tr '[:upper:]' '[:lower:]')_colors:
    src: abc
    dst: abc
  f_$(echo "${tmpd}" | sed -e 's#^/\(.*\)$#\1#g' | sed 's#/#_#g' | tr '[:upper:]' '[:lower:]')_mutt_colors:
    src: abc
    dst: abc
  f_$(echo "${tmpd}" | sed -e 's#^/tmp/\(.*\)$#\1#g' | sed 's#/#_#g' | tr '[:upper:]' '[:lower:]')_mutt_colors:
    src: abc
    dst: abc
profiles:
_EOF
cat "${cfg}"

# import
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V "${tmpd}"/.mutt/colors
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V "${tmpd}"/.colors

cat "${cfg}"

# ensure exists and is not link
[ ! -d "${tmps}"/dotfiles/"${tmpd}"/.mutt ] && echo "not a directory" && exit 1
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/.mutt/colors ] && echo "not exist" && exit 1
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/.colors ] && echo "not exist (2)" && exit 1

cat "${cfg}" | grep "${tmpd}"/.mutt/colors >/dev/null 2>&1
cat "${cfg}" | grep "${tmpd}"/.colors >/dev/null 2>&1

echo "OK"
exit 0
