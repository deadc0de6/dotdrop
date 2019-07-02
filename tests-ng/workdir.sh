#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test workdir relative or absolute
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
string="blabla"

# the dotfile source
tmp=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`

tmpf="${tmp}/dotfiles"
tmpw="${tmp}/workdir"

mkdir -p ${tmpf}
echo "dotfiles source (dotpath): ${tmpf}"
mkdir -p ${tmpw}
echo "workdir: ${tmpw}"

# create the config file
cfg="${tmp}/config.yaml"
echo "config file: ${cfg}"

# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
echo "dotfiles destination: ${tmpd}"

## RELATIVE
echo "RUNNING RELATIVE"
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  workdir: `echo ${tmpw} | sed 's/^.*\///g'`
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    link: true
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo "{{@@ profile @@}}" > ${tmpf}/abc
echo "${string}" >> ${tmpf}/abc

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -b -V

# checks
grep -r p1 ${tmpw} >/dev/null
grep -r ${string} ${tmpw} >/dev/null
[ ! -e ${tmpd}/abc ] && echo "[ERROR] dotfile not installed" && exit 1
[ ! -h ${tmpd}/abc ] && echo "[ERROR] dotfile is not a symlink" && exit 1

## CLEANING
rm -rf ${tmp} ${tmpd}

## ABSOLUTE
echo "RUNNING ABSOLUTE"
# the dotfile source
tmp=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`

tmpf="${tmp}/dotfiles"
tmpw="${tmp}/workdir"

mkdir -p ${tmpf}
echo "dotfiles source (dotpath): ${tmpf}"
mkdir -p ${tmpw}
echo "workdir: ${tmpw}"

# create the config file
cfg="${tmp}/config.yaml"
echo "config file: ${cfg}"

# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
echo "dotfiles destination: ${tmpd}"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  workdir: ${tmpw}
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    link: true
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo "{{@@ profile @@}}" > ${tmpf}/abc
echo "${string}" >> ${tmpf}/abc

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -b -V

# checks
grep -r p1 ${tmpw} >/dev/null
grep -r ${string} ${tmpw} >/dev/null
[ ! -e ${tmpd}/abc ] && echo "[ERROR] dotfile not installed" && exit 1
[ ! -h ${tmpd}/abc ] && echo "[ERROR] dotfile is not a symlink" && exit 1

## CLEANING
rm -rf ${tmp} ${tmpd}

## NONE
echo "RUNNING UNDEFINED WORKDIR"
# the dotfile source
tmp=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`

tmpf="${tmp}/dotfiles"

mkdir -p ${tmpf}
echo "dotfiles source (dotpath): ${tmpf}"

# create the config file
cfg="${tmp}/config.yaml"
echo "config file: ${cfg}"

# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
echo "dotfiles destination: ${tmpd}"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    link: true
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo "{{@@ profile @@}}" > ${tmpf}/abc
echo "${string}" >> ${tmpf}/abc

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -b -V

# checks
#grep -r p1 ${tmpw} >/dev/null
#grep -r ${string} ${tmpw} >/dev/null
[ ! -e ${tmpd}/abc ] && echo "[ERROR] dotfile not installed" && exit 1
[ ! -h ${tmpd}/abc ] && echo "[ERROR] dotfile is not a symlink" && exit 1

## CLEANING
rm -rf ${tmp} ${tmpd}

echo "OK"
exit 0
