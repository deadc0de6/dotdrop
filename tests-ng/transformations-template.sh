#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test transformations using templates
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

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
trans_read:
  r_echo_abs_src: echo "\$(cat {0}); {{@@ _dotfile_abs_src @@}}" > {1}
  r_echo_var: echo "\$(cat {0}); {{@@ r_var @@}}" > {1}
  reverse_it: cat {0} | rev > {1}
trans_write:
  w_echo_key: echo "\$(cat {0}); {{@@ _dotfile_key @@}}" > {1}
  w_echo_var: echo "\$(cat {0}); {{@@ w_var @@}}" > {1}
variables:
  r_var: readvar
  w_var: writevar
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_def:
    dst: ${tmpd}/def
    src: def
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    trans_read: r_echo_abs_src
    trans_write: w_echo_key
  f_ghi:
    dst: ${tmpd}/ghi
    src: ghi
    trans_read: r_echo_var
    trans_write: w_echo_var
  f_rev:
    dst: ${tmpd}/rev
    src: rev
    trans_read: reverse_it
profiles:
  p1:
    dotfiles:
    - f_abc
    - f_def
    - f_ghi
    - f_rev
_EOF
#cat ${cfg}

# create the dotfiles
echo 'abc' > "${tmps}"/dotfiles/abc
echo 'marker' > "${tmps}"/dotfiles/def
echo 'ghi' > "${tmps}"/dotfiles/ghi
echo '{{@@ profile @@}}' | rev > "${tmps}"/dotfiles/rev

###########################
# test install and compare
###########################

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b -V

# check dotfile
[ ! -e "${tmpd}"/def ] && exit 1
[ ! -e "${tmpd}"/abc ] && exit 1
[ ! -e "${tmpd}"/ghi ] && exit 1
[ ! -e "${tmpd}"/rev ] && exit 1
grep marker "${tmpd}"/def
cat "${tmpd}"/abc
grep "^abc; ${tmps}/dotfiles/abc$" "${tmpd}"/abc
cat "${tmpd}"/ghi
grep "^ghi; readvar$" "${tmpd}"/ghi
cat "${tmpd}"/rev
grep "^p1$" "${tmpd}"/rev

###########################
# test update
###########################

# update single file
cd "${ddpath}" | ${bin} update -f -k -c "${cfg}" -p p1 -b -V

# checks
[ ! -e "${tmps}"/dotfiles/def ] && exit 1
[ ! -e "${tmps}"/dotfiles/abc ] && exit 1
[ ! -e "${tmps}"/dotfiles/ghi ] && exit 1
[ ! -e "${tmps}"/dotfiles/rev ] && exit 1
grep marker "${tmps}"/dotfiles/def
cat "${tmps}"/dotfiles/abc
grep "^abc; ${tmps}/dotfiles/abc; f_abc$" "${tmps}"/dotfiles/abc
cat "${tmps}"/dotfiles/ghi
grep "^ghi; readvar; writevar$" "${tmps}"/dotfiles/ghi

echo "OK"
exit 0
