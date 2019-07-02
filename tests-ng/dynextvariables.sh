#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test dynamic external variables
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
extvars="${tmps}/variables.yaml"
extdvars="${tmps}/dynvariables.yaml"
pvars="${tmps}/p1_vars.yaml"
pvarin="${tmps}/inprofile_vars.yaml"
pvarout="${tmps}/outprofile_vars.yaml"
cfg="${tmps}/config.yaml"
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_variables:
  - "{{@@ var1 @@}}iables.yaml"
  - "{{@@ dvar1 @@}}iables.yaml"
  - "{{@@ profile @@}}_vars.yaml"
  - "{{@@ xvar @@}}_vars.yaml"
variables:
  var1: "var"
  xvar: outprofile
dynvariables:
  dvar1: "echo dynvar"
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
    variables:
      xvar: inprofile
_EOF
#cat ${cfg}

# create the external variables file
cat > ${extvars} << _EOF
variables:
  vara: "extvar1"
dynvariables:
  dvara: "echo extdvar1"
_EOF
cat > ${extdvars} << _EOF
variables:
  varb: "extvar2"
dynvariables:
  dvarb: "echo extdvar2"
_EOF
cat > ${pvars} << _EOF
variables:
  pvar: "pvar1"
dynvariables:
  pdvar: "echo pdvar1"
_EOF
cat > ${pvarin} << _EOF
variables:
  test: profileok
_EOF
cat > ${pvarout} << _EOF
variables:
  test: profilenotok
_EOF

# create the dotfile
echo "var1: {{@@ var1 @@}}" > ${tmps}/dotfiles/abc
echo "dvar1: {{@@ dvar1 @@}}" >> ${tmps}/dotfiles/abc
# from var file 1
echo "vara: {{@@ vara @@}}" >> ${tmps}/dotfiles/abc
echo "dvara: {{@@ dvara @@}}" >> ${tmps}/dotfiles/abc
# from var file 2
echo "varb: {{@@ varb @@}}" >> ${tmps}/dotfiles/abc
echo "dvarb: {{@@ dvarb @@}}" >> ${tmps}/dotfiles/abc
# from var file 3
echo "pvar: {{@@ pvar @@}}" >> ${tmps}/dotfiles/abc
echo "pdvar: {{@@ pdvar @@}}" >> ${tmps}/dotfiles/abc
# from profile variable
echo "test: {{@@ test @@}}" >> ${tmps}/dotfiles/abc

#cat ${tmps}/dotfiles/abc

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

cat ${tmpd}/abc

grep '^var1: var' ${tmpd}/abc >/dev/null
grep '^dvar1: dynvar' ${tmpd}/abc >/dev/null
grep '^vara: extvar1' ${tmpd}/abc >/dev/null
grep '^dvara: extdvar1' ${tmpd}/abc >/dev/null
grep '^varb: extvar2' ${tmpd}/abc >/dev/null
grep '^dvarb: extdvar2' ${tmpd}/abc >/dev/null
grep '^pvar: pvar1' ${tmpd}/abc >/dev/null
grep '^pdvar: pdvar1' ${tmpd}/abc >/dev/null
grep '^test: profileok' ${tmpd}/abc >/dev/null

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
