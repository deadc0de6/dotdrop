#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test the use of the keyword "import" in profiles
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
extdotfiles="${tmps}/df_p1.yaml"

dynextdotfiles_name="d_uid_dynvar"
dynextdotfiles="${tmps}/ext_${dynextdotfiles_name}"

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dynvariables:
  d_uid: "echo ${dynextdotfiles_name}"
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
  f_dyn:
    dst: ${tmpd}/dyn
    src: dyn
profiles:
  p1:
    dotfiles:
    - f_abc
    import:
    - $(basename ${extdotfiles})
    - "ext_{{@@ d_uid @@}}"
_EOF

# create the external dotfile file
cat > ${extdotfiles} << _EOF
dotfiles:
  - f_def
  - f_xyz
_EOF

cat > ${dynextdotfiles} << _EOF
dotfiles:
  - f_dyn
_EOF

# create the source
mkdir -p ${tmps}/dotfiles/
echo "abc" > ${tmps}/dotfiles/abc
echo "def" > ${tmps}/dotfiles/def
echo "xyz" > ${tmps}/dotfiles/xyz
echo "dyn" > ${tmps}/dotfiles/dyn

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

# checks
[ ! -e ${tmpd}/abc ] && exit 1
[ ! -e ${tmpd}/def ] && exit 1
[ ! -e ${tmpd}/xyz ] && exit 1
[ ! -e ${tmpd}/dyn ] && exit 1
echo 'file found'
grep 'abc' ${tmpd}/abc >/dev/null 2>&1
grep 'def' ${tmpd}/def >/dev/null 2>&1
grep 'xyz' ${tmpd}/xyz >/dev/null 2>&1
grep 'dyn' ${tmpd}/dyn >/dev/null 2>&1

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
