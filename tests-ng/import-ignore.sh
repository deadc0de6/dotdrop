#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2020, deadc0de6
#
# test ignore import
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
hash coverage 2>/dev/null && bin="coverage run -a --source=dotdrop -m dotdrop.dotdrop" || true

echo "dotdrop path: ${ddpath}"
echo "pythonpath: ${PYTHONPATH}"

# get the helpers
source ${cur}/helpers

echo -e "$(tput setaf 6)==> RUNNING $(basename $BASH_SOURCE) <==$(tput sgr0)"

################################################################
# this is the test
################################################################

# $1 pattern
# $2 path
grep_or_fail()
{
  grep "${1}" "${2}" >/dev/null 2>&1 || (echo "pattern not found in ${2}" && exit 1)
}

# the dotfile source
tmps=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
mkdir -p ${tmps}/dotfiles
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# dotdrop directory
mkdir -p ${tmpd}
mkdir -p ${tmpd}/a/{b,c}
echo 'a' > ${tmpd}/a/b/abfile
echo 'a' > ${tmpd}/a/c/acfile
echo 'a' > ${tmpd}/a/b/newfile
mkdir -p ${tmpd}/a/newdir
echo 'a' > ${tmpd}/a/newdir/newfile

# create the config file
cfg="${tmps}/config.yaml"
cat > ${cfg} << _EOF
config:
  backup: false
  create: true
  dotpath: dotfiles
  impignore:
  - "*/cfile"
  - "*/newfile"
  - "newdir"
dotfiles:
profiles:
_EOF
#cat ${cfg}

# import
echo "[+] import"
cd ${ddpath} | ${bin} import -c ${cfg} --verbose --profile=p1 ${tmpd}/a

[ -d ${tmps}/dotfiles/newdir ] && echo "newdir not ignored" && exit 1
[ -e ${tmps}/dotfiles/newdir/newfile ] && echo "newfile not ignored" && exit 1
[ -e ${tmps}/dotfiles/a/b/newfile ] && echo "newfile not ignored" && exit 1

echo "OK"
exit 0
