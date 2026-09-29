#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2026, deadc0de6
#
# test profile group, description and hidden (underscore) profiles
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
  f_xyz:
    dst: ${tmpd}/xyz
    src: xyz
profiles:
  p0:
    dotfiles:
    - f_abc
  _base:
    group: meta
    description: base profile for all hosts
    dotfiles:
    - f_abc
  zsh:
    group: meta
    dotfiles:
    - f_def
  home:
    group: hosts
    description: home workstation
    include:
    - _base
    - zsh
    dotfiles:
    - f_xyz
  office:
    group: hosts
    dotfiles:
    - f_xyz
_EOF

# create the dotfiles
echo "abc" > "${tmps}"/dotfiles/abc
echo "def" > "${tmps}"/dotfiles/def
echo "xyz" > "${tmps}"/dotfiles/xyz

# grepable: hidden profiles are not displayed
out=$(cd "${ddpath}" | ${bin} profiles -c "${cfg}" --grepable --verbose)
echo "${out}" | grep -q '^p0$'
echo "${out}" | grep -q '^zsh$'
echo "${out}" | grep -q '^home$'
echo "${out}" | grep -q '^office$'
if echo "${out}" | grep -q '^_base$'; then
  echo "hidden profile _base should not be grepable"
  exit 1
fi

# non grepable: profiles are grouped
out=$(cd "${ddpath}" | ${bin} profiles -c "${cfg}" --verbose)
# ungrouped profile first, with no group header in front of it
echo "${out}" | grep -q '\-> p0 (1 dotfiles)$'
# group headers present
echo "${out}" | grep -q '^group "meta":$'
echo "${out}" | grep -q '^group "hosts":$'
# description displayed
echo "${out}" | grep -q '\-> home (3 dotfiles) - home workstation'
# hidden profile not displayed
if echo "${out}" | grep -q '\-> _base'; then
  echo "hidden profile _base should not be displayed"
  exit 1
fi

# no group header for an empty (fully hidden) group
cfg2="${tmps}/config2.yaml"
cat > "${cfg2}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  home:
    group: hosts
    dotfiles:
    - f_abc
  _base:
    group: meta
    dotfiles:
    - f_abc
_EOF
out=$(cd "${ddpath}" | ${bin} profiles -c "${cfg2}" --verbose)
echo "${out}" | grep -q '^group "hosts":$'
if echo "${out}" | grep -q '^group "meta":$'; then
  echo "group meta is empty since hidden, should not be displayed"
  exit 1
fi

# hidden profile cannot be installed without force
set +e
cd "${ddpath}" | ${bin} install -c "${cfg}" -p _base --verbose
[ "$?" = "0" ] && echo "install of hidden profile should have failed" && exit 1
set -e
[ ! -e "${tmpd}"/abc ]

# hidden profile can be installed with force
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p _base --verbose
[ -e "${tmpd}"/abc ] && [ "$(cat "${tmpd}"/abc)" = "abc" ]

# profile including a hidden profile installs fine
rm -f "${tmpd}"/abc "${tmpd}"/def "${tmpd}"/xyz
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p home --verbose
[ -e "${tmpd}"/abc ] && [ "$(cat "${tmpd}"/abc)" = "abc" ]
[ -e "${tmpd}"/def ] && [ "$(cat "${tmpd}"/def)" = "def" ]
[ -e "${tmpd}"/xyz ] && [ "$(cat "${tmpd}"/xyz)" = "xyz" ]

# bad values for the new entries result in an error
set +e
cat > "${cfg2}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  bad:
    group: 42
    dotfiles:
    - f_abc
_EOF
cd "${ddpath}" | ${bin} profiles -c "${cfg2}"
[ "$?" = "0" ] && echo "bad group value should have failed" && exit 1
set -e

set +e
cat > "${cfg2}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  bad:
    description: [1, 2]
    dotfiles:
    - f_abc
_EOF
cd "${ddpath}" | ${bin} profiles -c "${cfg2}"
[ "$?" = "0" ] && echo "bad description value should have failed" && exit 1
set -e

echo "OK"
exit 0
