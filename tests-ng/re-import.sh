#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test re-importing file
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

clean()
{
  rm -rf ${tmps} ${tmpd} ~/.dotdrop-test
}

# the dotfile source
tmps=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
mkdir -p ${tmps}/dotfiles
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
#echo "dotfile destination: ${tmpd}"

# create the dotfile
echo "original" > ${tmpd}/testfile

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF
#cat ${cfg}

# import
echo "[+] import file"
cd ${ddpath} | ${bin} import -f -c ${cfg} -p p1 -V ${tmpd}/testfile
cat ${cfg}

# ensure exists and is not link
[ ! -e ${tmps}/dotfiles/${tmpd}/testfile ] && echo "does not exist" && clean && exit 1
cat ${cfg} | grep ${tmpd}/testfile >/dev/null 2>&1
grep 'original' ${tmps}/dotfiles/${tmpd}/testfile
nb=`cat ${cfg} | grep ${tmpd}/testfile | wc -l`
[ "${nb}" != "1" ] && echo 'not 1 entry' && clean && exit 1

# re-import without changing
echo "[+] re-import without changes"
cd ${ddpath} | ${bin} import -f -c ${cfg} -p p1 -V ${tmpd}/testfile
cat ${cfg}

# test is only once
[ ! -e ${tmps}/dotfiles/${tmpd}/testfile ] && echo "does not exist" && clean && exit 1
cat ${cfg} | grep ${tmpd}/testfile >/dev/null 2>&1
grep 'original' ${tmps}/dotfiles/${tmpd}/testfile
nb=`cat ${cfg} | grep ${tmpd}/testfile | wc -l`
[ "${nb}" != "1" ] && echo 'two entries!' && clean && exit 1

# re-import with changes
echo "[+] re-import with changes"
echo 'modified' > ${tmpd}/testfile
cd ${ddpath} | ${bin} import -f -c ${cfg} -p p1 -V ${tmpd}/testfile
cat ${cfg}

# test is only once
[ ! -e ${tmps}/dotfiles/${tmpd}/testfile ] && echo "does not exist" && clean && exit 1
cat ${cfg} | grep ${tmpd}/testfile >/dev/null 2>&1
grep 'modified' ${tmps}/dotfiles/${tmpd}/testfile
nb=`cat ${cfg} | grep ${tmpd}/testfile | wc -l`
[ "${nb}" != "1" ] && echo 'two entries!' && clean && exit 1

# ###################################################

echo 'original' > "${HOME}/.dotdrop.test"
# import in home
echo "[+] import file in home"
cd ${ddpath} | ${bin} import -f -c ${cfg} -p p1 -V ~/.dotdrop.test
cat ${cfg}

# ensure exists and is not link
[ ! -e "${tmps}/dotfiles/dotdrop.test" ] && echo "does not exist" && clean && exit 1
cat ${cfg} | grep "~/.dotdrop.test" >/dev/null 2>&1
grep 'original' ${tmps}/dotfiles/dotdrop.test
nb=`cat ${cfg} | grep "~/.dotdrop.test" | wc -l`
[ "${nb}" != "1" ] && echo 'not 1 entry' && clean && exit 1

# re-import without changing
echo "[+] re-import without changes in home"
cd ${ddpath} | ${bin} import -f -c ${cfg} -p p1 -V ~/.dotdrop.test
cat ${cfg}

# test is only once
[ ! -e "${tmps}/dotfiles/dotdrop.test" ] && echo "does not exist" && clean && exit 1
cat ${cfg} | grep "~/.dotdrop.test" >/dev/null 2>&1
grep 'original' ${tmps}/dotfiles/dotdrop.test
nb=`cat ${cfg} | grep "~/.dotdrop.test" | wc -l`
[ "${nb}" != "1" ] && echo 'two entries!' && clean && exit 1

# re-import with changes
echo "[+] re-import with changes in home"
echo 'modified' > ~/.dotdrop.test
cd ${ddpath} | ${bin} import -f -c ${cfg} -p p1 -V ~/.dotdrop.test
cat ${cfg}

# test is only once
[ ! -e "${tmps}/dotfiles/dotdrop.test" ] && echo "does not exist" && clean && exit 1
cat ${cfg} | grep "~/.dotdrop.test" >/dev/null 2>&1
grep 'modified' ${tmps}/dotfiles/dotdrop.test
nb=`cat ${cfg} | grep "~/.dotdrop.test" | wc -l`
[ "${nb}" != "1" ] && echo 'two entries!' && clean && exit 1

## CLEANING
clean

echo "OK"
exit 0
