#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test updates with key
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
basedir=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"

# the dotfile to be imported
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`

# originally imported directory
echo 'unique' > ${tmpd}/uniquefile
uniquefile_key="f_uniquefile"
echo 'unique2' > ${tmpd}/uniquefile2
uniquefile2_key="f_uniquefile2"
mkdir ${tmpd}/dir1
touch ${tmpd}/dir1/dir1f1
mkdir ${tmpd}/dir1/dir1dir1
dir1_key="d_dir1"

# create the config file
cfg="${basedir}/config.yaml"
create_conf ${cfg} # sets token

# import dir1
echo "[+] import"
cd ${ddpath} | ${bin} import -c ${cfg} ${tmpd}/dir1
cd ${ddpath} | ${bin} import -c ${cfg} ${tmpd}/uniquefile
cd ${ddpath} | ${bin} import -c ${cfg} ${tmpd}/uniquefile2

# make some modification
echo "[+] modify"
echo 'changed' > ${tmpd}/uniquefile
echo 'changed' > ${tmpd}/uniquefile2
echo 'new' > ${tmpd}/dir1/dir1dir1/new

# update by key
echo "[+] updating single key"
cd ${ddpath} | ${bin} update -c ${cfg} -k -f --verbose ${uniquefile_key}

# ensure changes applied correctly (only to uniquefile)
diff ${tmpd}/uniquefile ${basedir}/dotfiles/${tmpd}/uniquefile # should be same
set +e
diff ${tmpd}/uniquefile2 ${basedir}/dotfiles/${tmpd}/uniquefile2 # should be different
[ "${?}" != "1" ] && exit 1
set -e

# update all keys
echo "[+] updating all keys"
cd ${ddpath} | ${bin} update -c ${cfg} -k -f --verbose

# ensure all changes applied
diff ${tmpd} ${basedir}/dotfiles/${tmpd}

## CLEANING
rm -rf ${basedir} ${tmpd}

echo "OK"
exit 0
