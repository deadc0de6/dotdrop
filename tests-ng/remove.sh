#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test remove
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

# dotdrop directory
tmps=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
mkdir -p ${tmps}/dotfiles
# the dotfile to be imported
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
  f_def:
    dst: ${tmpd}/def
    src: def
  f_last:
    dst: ${tmpd}/last
    src: last
profiles:
  p1:
    dotfiles:
    - f_abc
    - f_def
  p2:
    dotfiles:
    - f_def
  last:
    dotfiles:
    - f_last
_EOF
cfgbak="${tmps}/config.yaml.bak"
cp ${cfg} ${cfgbak}

# create the dotfile
echo "abc" > ${tmps}/dotfiles/abc
echo "abc" > ${tmpd}/abc

echo "def" > ${tmps}/dotfiles/def
echo "def" > ${tmpd}/def

# remove with bad profile
cd ${ddpath} | ${bin} remove -f -k -p empty -c ${cfg} f_abc -V
[ ! -e ${tmps}/dotfiles/abc ] && echo "dotfile in dotpath deleted" && exit 1
[ ! -e ${tmpd}/abc ] && echo "source dotfile deleted" && exit 1
[ ! -e ${tmps}/dotfiles/def ] && echo "dotfile in dotpath deleted" && exit 1
[ ! -e ${tmpd}/def ] && echo "source dotfile deleted" && exit 1
# ensure config not altered
diff ${cfg} ${cfgbak}

# remove by key
echo "[+] remove f_abc by key"
cd ${ddpath} | ${bin} remove -p p1 -f -k -c ${cfg} f_abc -V
cat ${cfg}
echo "[+] remove f_def by key"
cd ${ddpath} | ${bin} remove -p p2 -f -k -c ${cfg} f_def -V
cat ${cfg}

# checks
[ -e ${tmps}/dotfiles/abc ] && echo "dotfile in dotpath not deleted" && exit 1
[ ! -e ${tmpd}/abc ] && echo "source dotfile deleted" && exit 1

[ -e ${tmps}/dotfiles/def ] && echo "dotfile in dotpath not deleted" && exit 1
[ ! -e ${tmpd}/def ] && echo "source dotfile deleted" && exit 1

echo "[+] ========="

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
  f_last:
    dst: ${tmpd}/last
    src: last
profiles:
  p1:
    dotfiles:
    - f_abc
    - f_def
  p2:
    dotfiles:
    - f_def
  last:
    dotfiles:
    - f_last
_EOF
cat ${cfg}

# create the dotfile
echo "abc" > ${tmps}/dotfiles/abc
echo "abc" > ${tmpd}/abc

echo "def" > ${tmps}/dotfiles/def
echo "def" > ${tmpd}/def

# remove by key
echo "[+] remove f_abc by path"
cd ${ddpath} | ${bin} remove -p p1 -f -c ${cfg} ${tmpd}/abc -V
cat ${cfg}
echo "[+] remove f_def by path"
cd ${ddpath} | ${bin} remove -p p2 -f -c ${cfg} ${tmpd}/def -V
cat ${cfg}

# checks
[ -e ${tmps}/dotfiles/abc ] && echo "(2) dotfile in dotpath not deleted" && exit 1
[ ! -e ${tmpd}/abc ] && echo "(2) source dotfile deleted" && exit 1

[ -e ${tmps}/dotfiles/def ] && echo "(2) dotfile in dotpath not deleted" && exit 1
[ ! -e ${tmpd}/def ] && echo "(2) source dotfile deleted" && exit 1


cat ${cfg}

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
