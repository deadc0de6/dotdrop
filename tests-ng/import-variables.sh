#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# import variables from file
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
hash coverage 2>/dev/null && bin="coverage run -a --source=dotdrop -m dotdrop.dotdrop" || true

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

# create the config file
cfg1="${tmps}/config1.yaml"
cfg2="${tmps}/config2.yaml"
varf="${tmps}/variables.yaml"

cat > ${cfg1} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_configs:
  - ${cfg2}
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p0:
    dotfiles:
    - f_abc
_EOF

cat > ${cfg2} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles-other
  import_variables:
  - ${varf}
dotfiles:
profiles:
_EOF

cat > ${varf} << _EOF
variables:
  var1: var1value
dynvariables:
  dvar1: "echo dvar1value"
_EOF

# create the source
mkdir -p ${tmps}/dotfiles/
echo "start" > ${tmps}/dotfiles/abc
echo "{{@@ var1 @@}}" >> ${tmps}/dotfiles/abc
echo "{{@@ dvar1 @@}}" >> ${tmps}/dotfiles/abc
echo "end" >> ${tmps}/dotfiles/abc

# install
cd ${ddpath} | ${bin} install -c ${cfg1} -p p0 -V

# test file content
cat ${tmpd}/abc
grep 'var1value' ${tmpd}/abc >/dev/null 2>&1
grep 'dvar1value' ${tmpd}/abc >/dev/null 2>&1

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
