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

echo "RUNNING $(basename $BASH_SOURCE)"

################################################################
# this is the test
################################################################

# dotdrop directory
basedir=`mktemp -d`
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"

# the dotfile to be imported
tmpd=`mktemp -d`

# some files
mkdir -p ${tmpd}/{program,config}
touch ${tmpd}/program/a
touch ${tmpd}/config/a

# create the config file
cfg="${basedir}/config.yaml"
create_conf ${cfg} # sets token

# import
echo "[+] import"
cd ${ddpath} | ${bin} import -c ${cfg} ${tmpd}/program
cd ${ddpath} | ${bin} import -c ${cfg} ${tmpd}/config

# add files
echo "[+] add files"
touch ${tmpd}/program/b
touch ${tmpd}/config/b

# expects diff
echo "[+] comparing normal"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose
[ "$?" = "0" ] && exit 1
set -e

# expects one diff
echo "[+] comparing with ignore"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose --ignore=${tmpd}/config/b
[ "$?" = "0" ] && exit 1
set -e

# expects no diff
echo "[+] comparing with ignore pattern"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose --ignore=b
[ "$?" != "0" ] && exit 1
set -e

## CLEANING
rm -rf ${basedir} ${tmpd}

echo "OK"
exit 0
