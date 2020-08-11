#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test install ignore absolute/relative
# returns 1 in case of error
#

# exit on first error
#set -e

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

# dotdrop directory
basedir=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"

# the dotfile to be imported
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`

# some files
mkdir -p ${tmpd}/{program,config,vscode}
echo "some data" > ${tmpd}/program/a
echo "some data" > ${tmpd}/config/a
echo "some data" > ${tmpd}/vscode/extensions.txt
echo "some data" > ${tmpd}/vscode/keybindings.json

# create the config file
cfg="${basedir}/config.yaml"
create_conf ${cfg} # sets token

# import
echo "[+] import"
cd ${ddpath} | ${bin} import -c ${cfg} ${tmpd}/program
cd ${ddpath} | ${bin} import -c ${cfg} ${tmpd}/config
cd ${ddpath} | ${bin} import -c ${cfg} ${tmpd}/vscode

# add files on filesystem
echo "[+] add files"
echo "new data" > ${basedir}/dotfiles/${tmpd}/README.md
echo "new data" > ${basedir}/dotfiles/${tmpd}/vscode/README.md
echo "new data" > ${basedir}/dotfiles/${tmpd}/program/README.md
mkdir -p ${basedir}/dotfiles/${tmpd}/readmes
echo "new data" > ${basedir}/dotfiles/${tmpd}/readmes/README.md

# install
rm -rf ${tmpd}
echo "[+] install normal"
cd ${ddpath} | ${bin} install --showdiff -c ${cfg} --verbose
[ "$?" != "0" ] && exit 1
nb=`find ${tmpd} -iname 'README.md' | wc -l`
echo "(1) found ${nb} README.md file(s)"
[ "${nb}" != "2" ] && exit 1

# adding ignore in dotfile
cfg2="${basedir}/config2.yaml"
sed '/d_program:/a \ \ \ \ instignore:\n\ \ \ \ - "README.md"' ${cfg} > ${cfg2}
cat ${cfg2}

# install
rm -rf ${tmpd}
echo "[+] install with ignore in dotfile"
cd ${ddpath} | ${bin} install -c ${cfg2} --verbose
[ "$?" != "0" ] && exit 1
nb=`find ${tmpd} -iname 'README.md' | wc -l`
echo "(2) found ${nb} README.md file(s)"
[ "${nb}" != "1" ] && exit 1

# adding ignore in config
cfg2="${basedir}/config2.yaml"
sed '/^config:/a \ \ instignore:\n\ \ - "README.md"' ${cfg} > ${cfg2}
cat ${cfg2}

# install
rm -rf ${tmpd}
echo "[+] install with ignore in config"
cd ${ddpath} | ${bin} install -c ${cfg2} --verbose
[ "$?" != "0" ] && exit 1
nb=`find ${tmpd} -iname 'README.md' | wc -l`
echo "(3) found ${nb} README.md file(s)"
[ "${nb}" != "0" ] && exit 1

## CLEANING
rm -rf ${basedir} ${tmpd}

echo "OK"
exit 0
