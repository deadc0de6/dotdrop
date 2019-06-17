#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test external variables
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

echo -e "\e[96m\e[1m==> RUNNING $(basename $BASH_SOURCE) <==\e[0m"

################################################################
# this is the test
################################################################

# the dotfile source
tmps=`mktemp -d --suffix='-dotdrop-tests'`
mkdir -p ${tmps}/dotfiles
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests'`
#echo "dotfile destination: ${tmpd}"

# create the config file
extvars="${tmps}/variables.yaml"
cfg="${tmps}/config.yaml"
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_variables:
  - $(basename ${extvars})
variables:
  var1: "var1"
  var2: "{{@@ var1 @@}} var2"
  var3: "{{@@ var2 @@}} var3"
  var4: "{{@@ dvar4 @@}}"
  varx: "test"
dynvariables:
  dvar1: "echo dvar1"
  dvar2: "{{@@ dvar1 @@}} dvar2"
  dvar3: "{{@@ dvar2 @@}} dvar3"
  dvar4: "echo {{@@ var3 @@}}"
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
    variables:
      varx: profvarx
_EOF
#cat ${cfg}

# create the external variables file
cat > ${extvars} << _EOF
variables:
  var1: "extvar1"
  varx: "exttest"
dynvariables:
  dvar1: "echo extdvar1"
  evar1: "echo extevar1"
_EOF

# create the dotfile
echo "var3: {{@@ var3 @@}}" > ${tmps}/dotfiles/abc
echo "dvar3: {{@@ dvar3 @@}}" >> ${tmps}/dotfiles/abc
echo "var4: {{@@ var4 @@}}" >> ${tmps}/dotfiles/abc
echo "dvar4: {{@@ dvar4 @@}}" >> ${tmps}/dotfiles/abc
echo "varx: {{@@ varx @@}}" >> ${tmps}/dotfiles/abc
echo "evar1: {{@@ evar1 @@}}" >> ${tmps}/dotfiles/abc

#cat ${tmps}/dotfiles/abc

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

cat ${tmpd}/abc
grep '^var3: extvar1 var2 var3' ${tmpd}/abc >/dev/null
grep '^dvar3: extdvar1 dvar2 dvar3' ${tmpd}/abc >/dev/null
grep '^var4: echo extvar1 var2 var3' ${tmpd}/abc >/dev/null
grep '^dvar4: extvar1 var2 var3' ${tmpd}/abc >/dev/null
grep '^varx: profvarx' ${tmpd}/abc >/dev/null
grep '^evar1: extevar1' ${tmpd}/abc >/dev/null

rm -f ${tmpd}/abc

#cat ${tmpd}/abc
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_variables:
  - $(basename ${extvars})
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
    variables:
      varx: profvarx
_EOF
#cat ${cfg}

# create the external variables file
cat > ${extvars} << _EOF
variables:
  var1: "extvar1"
  varx: "exttest"
  var2: "{{@@ var1 @@}} var2"
  var3: "{{@@ var2 @@}} var3"
  var4: "{{@@ dvar4 @@}}"
dynvariables:
  dvar1: "echo extdvar1"
  dvar2: "{{@@ dvar1 @@}} dvar2"
  dvar3: "{{@@ dvar2 @@}} dvar3"
  dvar4: "echo {{@@ var3 @@}}"
_EOF

# create the dotfile
echo "var3: {{@@ var3 @@}}" > ${tmps}/dotfiles/abc
echo "dvar3: {{@@ dvar3 @@}}" >> ${tmps}/dotfiles/abc
echo "var4: {{@@ var4 @@}}" >> ${tmps}/dotfiles/abc
echo "dvar4: {{@@ dvar4 @@}}" >> ${tmps}/dotfiles/abc
echo "varx: {{@@ varx @@}}" >> ${tmps}/dotfiles/abc

#cat ${tmps}/dotfiles/abc

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

cat ${tmpd}/abc

grep '^var3: extvar1 var2 var3' ${tmpd}/abc >/dev/null
grep '^dvar3: extdvar1 dvar2 dvar3' ${tmpd}/abc >/dev/null
grep '^var4: echo extvar1 var2 var3' ${tmpd}/abc >/dev/null
grep '^dvar4: extvar1 var2 var3' ${tmpd}/abc >/dev/null
grep '^varx: profvarx' ${tmpd}/abc >/dev/null

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
