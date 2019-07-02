#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test updates
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
mkdir -p ${tmpd}/{program,config}
touch ${tmpd}/program/a
touch ${tmpd}/config/a
mkdir ${tmpd}/vscode
touch ${tmpd}/vscode/extensions.txt
touch ${tmpd}/vscode/keybindings.json

# create the config file
cfg="${basedir}/config.yaml"
create_conf ${cfg} # sets token

# import
echo "[+] import"
cd ${ddpath} | ${bin} import -c ${cfg} ${tmpd}/program
cd ${ddpath} | ${bin} import -c ${cfg} ${tmpd}/config
cd ${ddpath} | ${bin} import -c ${cfg} ${tmpd}/vscode

# add files
echo "[+] add files"
touch ${tmpd}/program/b
touch ${tmpd}/config/b

# expects diff
echo "[+] comparing normal - 2 diffs"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose
[ "$?" = "0" ] && exit 1
set -e

# expects one diff
patt="${tmpd}/config/b"
echo "[+] comparing with ignore (pattern: ${patt}) - 1 diff"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose --ignore=${patt}
[ "$?" = "0" ] && exit 1
set -e

# expects no diff
patt="*b"
echo "[+] comparing with ignore (pattern: ${patt}) - 0 diff"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose --ignore=${patt}
[ "$?" != "0" ] && exit 1
set -e

# expects one diff
patt="*/config/*b"
echo "[+] comparing with ignore (pattern: ${patt}) - 1 diff"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose --ignore=${patt}
[ "$?" = "0" ] && exit 1
set -e

#cat ${cfg}

# adding ignore in dotfile
cfg2="${basedir}/config2.yaml"
sed '/d_config:/a \ \ \ \ cmpignore:\n\ \ \ \ - "*/config/b"' ${cfg} > ${cfg2}
#cat ${cfg2}

# expects one diff
echo "[+] comparing with ignore in dotfile - 1 diff"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg2} --verbose
[ "$?" = "0" ] && exit 1
set -e

# adding ignore in dotfile
cfg2="${basedir}/config2.yaml"
sed '/d_config:/a \ \ \ \ cmpignore:\n\ \ \ \ - "*b"' ${cfg} > ${cfg2}
sed -i '/d_program:/a \ \ \ \ cmpignore:\n\ \ \ \ - "*b"' ${cfg2}
#cat ${cfg2}

# expects no diff
patt="*b"
echo "[+] comparing with ignore in dotfile - 0 diff"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg2} --verbose
[ "$?" != "0" ] && exit 1
set -e

# update files
echo touched > ${tmpd}/vscode/extensions.txt
echo touched > ${tmpd}/vscode/keybindings.json

# expect two diffs
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose -C ${tmpd}/vscode
[ "$?" = "0" ] && exit 1
set -e

# expects no diff
sed '/d_vscode:/a \ \ \ \ cmpignore:\n\ \ \ \ - "*extensions.txt"\n\ \ \ \ - "*keybindings.json"' ${cfg} > ${cfg2}
set +e
cd ${ddpath} | ${bin} compare -c ${cfg2} --verbose -C ${tmpd}/vscode
[ "$?" != "0" ] && exit 1
set -e

# clean
rm -rf ${basedir}/dotfiles
mkdir -p ${basedir}/dotfiles

# create dotfiles/dirs
mkdir -p ${tmpd}/{program,config,vscode}
touch ${tmpd}/program/a
touch ${tmpd}/config/a
touch ${tmpd}/vscode/extensions.txt
touch ${tmpd}/vscode/keybindings.json
touch ${tmpd}/vscode/keybindings.json

# create the config file
cfg="${basedir}/config3.yaml"
create_conf ${cfg} # sets token

# import
echo "[+] import"
cd ${ddpath} | ${bin} import -c ${cfg} ${tmpd}/program ${tmpd}/config ${tmpd}/vscode

# create the files to ignore
touch ${tmpd}/program/.DS_Store
touch ${tmpd}/config/.DS_Store
touch ${tmpd}/vscode/.DS_Store

# ensure not imported
found=`find ${basedir}/dotfiles/ -iname '.DS_Store'`
[ "${found}" != "" ] && echo "imported ???" && exit 1

# general ignore
echo "[+] comparing ..."
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose -i '*/.DS_Store'
[ "$?" != "0" ] && exit 1

# general ignore
echo "[+] comparing2  ..."
sed '/^config:$/a\ \ cmpignore:\n\ \ - "*/.DS_Store"' ${cfg} > ${cfg2}
cat ${cfg2}
cd ${ddpath} | ${bin} compare -c ${cfg2} --verbose
[ "$?" != "0" ] && exit 1

## CLEANING
rm -rf ${basedir} ${tmpd}

echo "OK"
exit 0
