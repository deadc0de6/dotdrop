#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test link of directory containing templates on home
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
echo "dotfiles source (dotpath): ${tmps}"
# the dotfile destination
tmpd=`mktemp -d -p ${HOME} --suffix='-dotdrop-tests' || mktemp -d`
echo "dotfiles destination: ${tmpd}"
# the workdir
tmpw=`mktemp -d -p ${HOME} --suffix='-dotdrop-tests' || mktemp -d`
echo "workdir: ${tmpw}"


# create the config file
cfg="${tmps}/config.yaml"

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
mkdir -p ${tmps}/dotfiles/abc
echo "{{@@ profile @@}}" > ${tmps}/dotfiles/abc/template
echo "blabla" >> ${tmps}/dotfiles/abc/template
echo "blabla" > ${tmps}/dotfiles/abc/nottemplate

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -b -V

# checks
[ ! -d ${tmpd}/abc ] && echo "[ERROR] dotfile not installed" && exit 1
[ ! -h ${tmpd}/abc ] && echo "[ERROR] dotfile is not a symlink" && exit 1
#cat ${tmpd}/abc/template
#tree -a ${tmpd}/abc/
set +e
grep '{{@@' ${tmpd}/abc/template >/dev/null 2>&1 && echo "[ERROR] template in dir not replace" && exit 1
set -e

## CLEANING
rm -rf ${tmps} ${tmpd} ${tmpw}

echo "OK"
exit 0
