#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2020, deadc0de6
#
# test chmod on install
# with files and directories
# with different link
#
# TODO
# - test for symlink templates
# - check for mode difference when install

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

# create the config file
cfg="${tmps}/config.yaml"

echo 'f777' > ${tmps}/dotfiles/f777
echo 'link' > ${tmps}/dotfiles/link
mkdir -p ${tmps}/dotfiles/dir
echo "f1" > ${tmps}/dotfiles/dir/f1

echo "exists" > ${tmps}/dotfiles/exists
chmod 644 ${tmps}/dotfiles/exists
echo "exists" > ${tmpd}/exists
chmod 644 ${tmpd}/exists

echo "existslink" > ${tmps}/dotfiles/existslink
chmod 644 ${tmpd}/exists

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_f777:
    src: f777
    dst: ${tmpd}/f777
    chmod: 777
  f_link:
    src: link
    dst: ${tmpd}/link
    chmod: 777
    link: link
  d_dir:
    src: dir
    dst: ${tmpd}/dir
    chmod: 777
  f_exists:
    src: exists
    dst: ${tmpd}/exists
    chmod: 777
  f_existslink:
    src: existslink
    dst: ${tmpd}/existslink
    chmod: 777
    link: link
profiles:
  p1:
    dotfiles:
    - f_f777
    - f_link
    - d_dir
    - f_exists
    - f_existslink
  p2:
    dotfiles:
    - f_exists
    - f_existslink
_EOF
#cat ${cfg}

# install
cd ${ddpath} | ${bin} install -c ${cfg} -f -p p1 -V ${i}

mode=`stat -c '%a' "${tmpd}/f777"`
[ "${mode}" != "777" ] && echo "bad mode for f777" && exit 1

mode=`stat -c '%a' "${tmpd}/link"`
[ "${mode}" != "777" ] && echo "bad mode for link" && exit 1

mode=`stat -c '%a' "${tmpd}/dir"`
[ "${mode}" != "777" ] && echo "bad mode for dir" && exit 1

mode=`stat -c '%a' "${tmpd}/exists"`
[ "${mode}" != "777" ] && echo "bad mode for exists" && exit 1

mode=`stat -c '%a' "${tmpd}/existslink"`
[ "${mode}" != "777" ] && echo "bad mode for existslink" && exit 1

echo "exists" > ${tmps}/dotfiles/exists
chmod 644 ${tmps}/dotfiles/exists
echo "exists" > ${tmpd}/exists
chmod 644 ${tmpd}/exists

chmod 644 ${tmpd}/existslink

cd ${ddpath} | ${bin} install -c ${cfg} -p p2 -V ${i}

mode=`stat -c '%a' "${tmpd}/exists"`
[ "${mode}" != "777" ] && echo "bad mode for exists" && exit 1

mode=`stat -c '%a' "${tmpd}/existslink"`
[ "${mode}" != "777" ] && echo "bad mode for existslink" && exit 1

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
