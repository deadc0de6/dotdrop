#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6
#
# test relative symlink
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
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

##################################################
# test symlink directory
##################################################
# create the dotfile
echo "file1" > ${tmps}/dotfiles/abc

# create the config file
cfg="${tmps}/config.yaml"
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_dotfile_default: nolink
dotfiles:
  d_abc:
    dst: ${tmpd}/abc
    src: abc
    link: relative
  d_abc2:
    dst: ${tmpd}/abc2
    src: abc
    link: absolute
profiles:
  p1:
    dotfiles:
    - d_abc
    - d_abc2
_EOF
#cat ${cfg}

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

# ensure exists and is link
[ ! -h ${tmpd}/abc ] && echo "not a symlink" && exit 1
[ ! -h ${tmpd}/abc2 ] && echo "not a symlink" && exit 1

ls -l ${tmpd}/abc | grep '..' || exit 1
ls -l ${tmpd}/abc2

grep 'file1' ${tmpd}/abc
grep 'file1' ${tmpd}/abc2

## TODO with templates
echo "TODO with templates"
exit 1

echo "OK"
exit 0
