#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2021, deadc0de6
#
# test key_prefix and key_separator
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
mkdir -p "${tmpd}"/top
touch "${tmpd}"/top/.colors
mkdir -p "${tmpd}"/.mutt/sub
touch "${tmpd}"/.mutt/sub/colors

# create the config file
cfg="${tmps}/config.yaml"

# normal behavior
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  longkey: true
  key_prefix: true
  key_separator: '_'
dotfiles:
profiles:
_EOF

# import
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V "${tmpd}"/top/.colors
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V "${tmpd}"/.mutt/sub

cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -G | cut -f1 -d',' | grep -q '_top_colors'
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -G | cut -f1 -d',' | grep -q '_mutt_sub'

cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -G | cut -f1 -d',' | grep '_top_colors' | grep -q 'f_'
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -G | cut -f1 -d',' | grep '_mutt_sub' | grep -q 'd_'

# pimping
rm -rf "${tmps:?}"/*

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  longkey: true
  key_prefix: false
  key_separator: '+'
dotfiles:
profiles:
_EOF

# import
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V "${tmpd}"/top/.colors
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V "${tmpd}"/.mutt/sub

cat "${cfg}"
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -G

cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -G | cut -f1 -d',' | grep -q '+top+colors'
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -G | cut -f1 -d',' | grep -q '+mutt+sub'

cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -G | cut -f1 -d',' | grep '+top+colors' | grep -qv 'f_'
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -G | cut -f1 -d',' | grep '+mutt+sub' | grep -qv 'd_'

echo "OK"
exit 0
