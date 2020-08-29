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
profiles:
  p0:
    dotfiles:
    - f_abc
variables:
  global: global_var
  local: local_var
_EOF

# create the source
mkdir -p ${tmps}/dotfiles/

cat > ${tmps}/dotfiles/macro_file << _EOF
{%@@ macro macro(var) @@%}
{{@@ global @@}}
{{@@ var @@}}
{%@@ endmacro @@%}
_EOF

cat > ${tmps}/dotfiles/abc << _EOF
{%@@ from 'macro_file' import macro @@%}
{{@@ macro(local) @@}}
_EOF

# install
cd ${ddpath} | ${bin} install -c ${cfg} -p p0 -V

# test file content
cat ${tmpd}/abc
grep 'global_var' ${tmpd}/abc >/dev/null 2>&1
grep 'local_var' ${tmpd}/abc >/dev/null 2>&1

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
