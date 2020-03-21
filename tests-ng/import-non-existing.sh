#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test import not existing
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

# create the dotfile
echo "test" > ${tmps}/dotfiles/abc

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_variables:
  - /variables/does/not/exist:optional
  - /variables/does/not/::exist:optional
  - /variables/*/not/exist:optional
  import_actions:
  - /actions/does/not/exist:optional
  - /actions/does/not/::exist:optional
  - /actions/does/*/exist:optional
  import_configs:
  - /configs/does/not/exist:optional
  - /configs/does/not/::exist:optional
  - /configs/does/not/*:optional
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# dummy call
cd ${ddpath} | ${bin} files -c ${cfg} -p p1 -V

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_variables:
  - /variables/does/not/exist
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# dummy call
set +e
cd ${ddpath} | ${bin} files -c ${cfg} -p p1 -V
[ "$?" = "0" ] && echo "variables" && exit 1
set -e

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_variables:
  - /variables/*/not/exist
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# dummy call
set +e
cd ${ddpath} | ${bin} files -c ${cfg} -p p1 -V
[ "$?" = "0" ] && echo "variables glob" && exit 1
set -e

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_actions:
  - /actions/does/not/exist
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# dummy call
set +e
cd ${ddpath} | ${bin} files -c ${cfg} -p p1 -V
[ "$?" = "0" ] && echo "actions" && exit 1
set -e

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_actions:
  - /actions/does/*/exist
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# dummy call
set +e
cd ${ddpath} | ${bin} files -c ${cfg} -p p1 -V
[ "$?" = "0" ] && echo "actions glob" && exit 1
set -e

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_configs:
  - /configs/does/not/exist
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# dummy call
set +e
cd ${ddpath} | ${bin} files -c ${cfg} -p p1 -V
[ "$?" = "0" ] && echo "configs" && exit 1
set -e

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_configs:
  - /configs/does/not/*
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# dummy call
set +e
cd ${ddpath} | ${bin} files -c ${cfg} -p p1 -V
[ "$?" = "0" ] && echo "configs glob" && exit 1
set -e

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
