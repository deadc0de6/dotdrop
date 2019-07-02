#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test jinja2 helpers from jhelpers
# returns 1 in case of error
#

# exit on first error
set -e

# all this crap to get current path
rl="readlink -f"
if ! ${rl} "${0}" >/dev/null 2>&1; then
  rl="realpath"

  if ! hash ${rl}; then
    echo "\"${rl}\" not found !" && exit 1
  fi
fi
cur=$(dirname "$(${rl} "${0}")")

#hash dotdrop >/dev/null 2>&1
#[ "$?" != "0" ] && echo "install dotdrop to run tests" && exit 1

#echo "called with ${1}"

# dotdrop path can be pass as argument
ddpath="${cur}/../"
[ "${1}" != "" ] && ddpath="${1}"
[ ! -d ${ddpath} ] && echo "ddpath \"${ddpath}\" is not a directory" && exit 1

export PYTHONPATH="${ddpath}:${PYTHONPATH}"
bin="python3 -m dotdrop.dotdrop"

echo "dotdrop path: ${ddpath}"
echo "pythonpath: ${PYTHONPATH}"

# get the helpers
source ${cur}/helpers

echo -e "$(tput setaf 6)==> RUNNING $(basename $BASH_SOURCE) <==$(tput sgr0)"

################################################################
# this is the test
################################################################

# the dotfile source
tmps=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
mkdir -p ${tmps}/dotfiles
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
#echo "dotfile destination: ${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
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
echo "this is the test dotfile" > ${tmps}/dotfiles/abc

# test exists
echo "{%@@ if exists('/dev/null') @@%}" >> ${tmps}/dotfiles/abc
echo "this should exist" >> ${tmps}/dotfiles/abc
echo "{%@@ endif @@%}" >> ${tmps}/dotfiles/abc

echo "{%@@ if exists('/dev/abcdef') @@%}" >> ${tmps}/dotfiles/abc
echo "this should not exist" >> ${tmps}/dotfiles/abc
echo "{%@@ endif @@%}" >> ${tmps}/dotfiles/abc

# test exists_in_path
cat >> ${tmps}/dotfiles/abc << _EOF
{%@@ if exists_in_path('cat') @@%}
this should exist too
{%@@ endif @@%}
_EOF

cat >> ${tmps}/dotfiles/abc << _EOF
{%@@ if exists_in_path('a_name_that_is_unlikely_to_be_chosen_for_an_executable') @@%}
this should not exist either
{%@@ endif @@%}
_EOF

#cat ${tmps}/dotfiles/abc

echo "this is def" > ${tmps}/dotfiles/def

# test basename
cat >> ${tmps}/dotfiles/def << _EOF
{%@@ set dotfile_filename = basename( _dotfile_abs_dst ) @@%}
dotfile dst filename: {{@@ dotfile_filename @@}}
_EOF

# test dirname
cat >> ${tmps}/dotfiles/def << _EOF
{%@@ set dotfile_dirname= dirname( _dotfile_abs_dst ) @@%}
dotfile dst dirname: {{@@ dotfile_dirname @@}}
_EOF

#cat ${tmps}/dotfiles/def

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

#cat ${tmpd}/abc

grep '^this should exist' ${tmpd}/abc >/dev/null
grep '^this should exist too' ${tmpd}/abc >/dev/null
set +e
grep '^this should not exist' ${tmpd}/abc >/dev/null && exit 1
grep '^this should not exist either' ${tmpd}/abc >/dev/null && exit 1
set -e

#cat ${tmpd}/abc

# test def
grep "dotfile dst filename: `basename ${tmpd}/def`" ${tmpd}/def
grep "dotfile dst dirname: `dirname ${tmpd}/def`" ${tmpd}/def

## CLEANING
rm -rf ${tmps} ${tmpd} ${scr}

echo "OK"
exit 0
