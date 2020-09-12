#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# import config testing
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
mkdir -p ${tmps}/dotfiles-other
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`

# create the config file
cfg1="${tmps}/config1.yaml"
cfg2="${tmps}/config2.yaml"

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
  f_zzz:
    dst: ${tmpd}/zzz
    src: zzz
  f_sub:
    dst: ${tmpd}/sub
    src: sub
profiles:
  p0:
    include:
    - p2
  p1:
    dotfiles:
    - f_abc
  p3:
    dotfiles:
    - f_zzz
  pup:
    include:
    - psubsub
_EOF

cat > ${cfg2} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles-other
dotfiles:
  f_def:
    dst: ${tmpd}/def
    src: def
  f_ghi:
    dst: ${tmpd}/ghi
    src: ghi
  f_asub:
    dst: ${tmpd}/subdir/sub/asub
    src: subdir/sub/asub
profiles:
  p2:
    dotfiles:
    - f_def
    - f_asub
  psubsub:
    dotfiles:
    - f_sub
_EOF

# create the source
mkdir -p ${tmps}/dotfiles/
echo "abc" > ${tmps}/dotfiles/abc
echo "{{@@ _dotfile_abs_dst @@}}" >> ${tmps}/dotfiles/abc

echo "def" > ${tmps}/dotfiles-other/def
echo "{{@@ _dotfile_abs_dst @@}}" >> ${tmps}/dotfiles-other/def

echo "ghi" > ${tmps}/dotfiles-other/ghi
echo "{{@@ _dotfile_abs_dst @@}}" >> ${tmps}/dotfiles-other/ghi

echo "zzz" > ${tmps}/dotfiles/zzz
echo "{{@@ _dotfile_abs_dst @@}}" >> ${tmps}/dotfiles/zzz

echo "sub" > ${tmps}/dotfiles/sub
echo "{{@@ _dotfile_abs_dst @@}}" >> ${tmps}/dotfiles/sub

mkdir -p ${tmps}/dotfiles-other/subdir/sub
echo "subsub" > ${tmps}/dotfiles-other/subdir/sub/asub
echo "{{@@ _dotfile_abs_dst @@}}" >> ${tmps}/dotfiles-other/subdir/sub/asub

# install
cd ${ddpath} | ${bin} files -c ${cfg1} -p p0 -V | grep f_def
cd ${ddpath} | ${bin} files -c ${cfg1} -p p1 -V | grep f_abc
cd ${ddpath} | ${bin} files -c ${cfg1} -p p2 -V | grep f_def
cd ${ddpath} | ${bin} files -c ${cfg1} -p p3 -V | grep f_zzz
cd ${ddpath} | ${bin} files -c ${cfg1} -p pup -V | grep f_sub
cd ${ddpath} | ${bin} files -c ${cfg1} -p psubsub -V | grep f_sub

# test compare too
cd ${ddpath} | ${bin} install -c ${cfg1} -p p2 -V
cd ${ddpath} | ${bin} compare -c ${cfg1} -p p2 -V

# test with non-existing dotpath this time
rm -rf ${tmps}/dotfiles
cat > ${cfg1} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_configs:
  - ${cfg2}
dotfiles:
profiles:
_EOF
cat > ${cfg2} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles-other
dotfiles:
  f_asub:
    dst: ${tmpd}/subdir/sub/asub
    src: subdir/sub/asub
profiles:
  p2:
    dotfiles:
    - f_asub
_EOF
cd ${ddpath} | ${bin} install -c ${cfg1} -p p2 -V
cd ${ddpath} | ${bin} compare -c ${cfg1} -p p2 -V

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
