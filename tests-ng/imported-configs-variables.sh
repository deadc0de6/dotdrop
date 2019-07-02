#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test external config's variables
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
extcfg="${tmps}/ext-config.yaml"
cfg="${tmps}/config.yaml"
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_configs:
  - $(basename ${extcfg})
variables:
  varx: "test"
  provar: "local"
dynvariables:
  dvarx: "echo dtest"
  dprovar: "echo dlocal"
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
      provar: provar
    dynvariables:
      dvarx: echo dprofvarx
      dprovar: echo dprovar
_EOF
cat ${cfg}

# create the external variables file
cat > ${extcfg} << _EOF
config:
profiles:
  p2:
    dotfiles:
    - f_abc
    variables:
      varx: extprofvarx
      provar: extprovar
    dynvariables:
      dvarx: echo extdprofvarx
      dprovar: echo extdprovar
dotfiles:
_EOF
ls -l ${extcfg}
cat ${extcfg}

# create the dotfile
echo "varx: {{@@ varx @@}}" > ${tmps}/dotfiles/abc
echo "provar: {{@@ provar @@}}" >> ${tmps}/dotfiles/abc
echo "dvarx: {{@@ dvarx @@}}" >> ${tmps}/dotfiles/abc
echo "dprovar: {{@@ dprovar@@}}" >> ${tmps}/dotfiles/abc

#cat ${tmps}/dotfiles/abc

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p2 -V

echo "test1"
cat ${tmpd}/abc
grep '^varx: extprofvarx' ${tmpd}/abc >/dev/null
grep '^provar: extprovar' ${tmpd}/abc >/dev/null
grep '^dvarx: extdprofvarx' ${tmpd}/abc >/dev/null
grep '^dprovar: extdprovar' ${tmpd}/abc >/dev/null

rm -f ${tmpd}/abc
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

echo "test2"
cat ${tmpd}/abc
grep '^varx: profvarx' ${tmpd}/abc >/dev/null
grep '^provar: provar' ${tmpd}/abc >/dev/null
grep '^dvarx: dprofvarx' ${tmpd}/abc >/dev/null
grep '^dprovar: dprovar' ${tmpd}/abc >/dev/null

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
