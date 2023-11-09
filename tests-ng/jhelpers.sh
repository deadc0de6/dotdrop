#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test jinja2 helpers from jhelpers
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
#echo "dotfile destination: ${tmpd}"

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
  p1:
    dotfiles:
    - f_abc
    - f_def
_EOF
#cat ${cfg}

# create the dotfile
echo "this is the test dotfile" > "${tmps}"/dotfiles/abc

# test exists
echo "{%@@ if exists('/dev/null') @@%}" >> "${tmps}"/dotfiles/abc
echo "this should exist" >> "${tmps}"/dotfiles/abc
echo "{%@@ endif @@%}" >> "${tmps}"/dotfiles/abc

echo "{%@@ if exists('/dev/abcdef') @@%}" >> "${tmps}"/dotfiles/abc
echo "this should not exist" >> "${tmps}"/dotfiles/abc
echo "{%@@ endif @@%}" >> "${tmps}"/dotfiles/abc

# test exists_in_path
cat >> "${tmps}"/dotfiles/abc << _EOF
{%@@ if exists_in_path('cat') @@%}
this should exist too
{%@@ endif @@%}
_EOF

cat >> "${tmps}"/dotfiles/abc << _EOF
{%@@ if exists_in_path('a_name_that_is_unlikely_to_be_chosen_for_an_executable') @@%}
this should not exist either
{%@@ endif @@%}
_EOF

#cat ${tmps}/dotfiles/abc

echo "this is def" > "${tmps}"/dotfiles/def

# test basename
cat >> "${tmps}"/dotfiles/def << _EOF
{%@@ set dotfile_filename = basename( _dotfile_abs_dst ) @@%}
dotfile dst filename: {{@@ dotfile_filename @@}}
_EOF

# test dirname
cat >> "${tmps}"/dotfiles/def << _EOF
{%@@ set dotfile_dirname= dirname( _dotfile_abs_dst ) @@%}
dotfile dst dirname: {{@@ dotfile_dirname @@}}
_EOF

#cat ${tmps}/dotfiles/def

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

#cat ${tmpd}/abc

grep '^this should exist' "${tmpd}"/abc >/dev/null
grep '^this should exist too' "${tmpd}"/abc >/dev/null
set +e
grep '^this should not exist' "${tmpd}"/abc >/dev/null && exit 1
grep '^this should not exist either' "${tmpd}"/abc >/dev/null && exit 1
set -e

#cat ${tmpd}/abc

# test def
grep "dotfile dst filename: $(basename "${tmpd}"/def)" "${tmpd}"/def
grep "dotfile dst dirname: $(dirname "${tmpd}"/def)" "${tmpd}"/def

echo "OK"
exit 0
