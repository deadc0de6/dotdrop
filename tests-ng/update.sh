#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test updates
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

# single file
echo 'unique' > ${tmpd}/uniquefile

# hierarchy from https://pymotw.com/2/filecmp/
# create the hierarchy
# for dir1 (originally imported directory))))
mkdir ${tmpd}/dir1
touch ${tmpd}/dir1/file_only_in_dir1
mkdir -p ${tmpd}/dir1/dir_only_in_dir1
mkdir -p ${tmpd}/dir1/common_dir
echo 'this file is the same' > ${tmpd}/dir1/common_file
echo 'in dir1' > ${tmpd}/dir1/not_the_same
echo 'This is a file in dir1' > ${tmpd}/dir1/file_in_dir1
mkdir -p ${tmpd}/dir1/sub/sub2
mkdir -p ${tmpd}/dir1/notindir2/notindir2
echo 'first' > ${tmpd}/dir1/sub/sub2/different
#tree ${tmpd}/dir1

# create the hierarchy
# for dir2 (modified original for update)
mkdir ${tmpd}/dir2
touch ${tmpd}/dir2/file_only_in_dir2
mkdir -p ${tmpd}/dir2/dir_only_in_dir2
mkdir -p ${tmpd}/dir2/common_dir
echo 'this file is the same' > ${tmpd}/dir2/common_file
echo 'in dir2' > ${tmpd}/dir2/not_the_same
mkdir -p ${tmpd}/dir2/file_in_dir1
mkdir -p ${tmpd}/dir2/sub/sub2
echo 'modified' > ${tmpd}/dir2/sub/sub2/different
mkdir -p ${tmpd}/dir2/new/new2
mkdir -p ${tmpd}/dir2/sub1/sub2/sub3/
touch ${tmpd}/dir2/sub1/sub2/sub3/file
#tree ${tmpd}/dir2

# create the config file
cfg="${basedir}/config.yaml"
create_conf ${cfg} # sets token

# import dir1
echo "[+] import"
cd ${ddpath} | ${bin} import -c ${cfg} ${tmpd}/dir1
cd ${ddpath} | ${bin} import -c ${cfg} ${tmpd}/uniquefile

# let's see the dotpath
#tree ${basedir}/dotfiles

# change dir1 to dir2 in deployed
echo "[+] change dir"
rm -rf ${tmpd}/dir1
mv ${tmpd}/dir2 ${tmpd}/dir1
#tree ${tmpd}/dir1

# change unique file
echo 'changed' > ${tmpd}/uniquefile

# compare
#echo "[+] comparing"
#cd ${ddpath} | ${bin} compare -c ${cfg}

# update
echo "[+] updating"
cd ${ddpath} | ${bin} update -c ${cfg} -f --verbose ${tmpd}/uniquefile ${tmpd}/dir1

# manually update
rm ${basedir}/dotfiles/${tmpd}/dir1/file_in_dir1
mkdir -p ${basedir}/dotfiles/${tmpd}/dir1/file_in_dir1

# ensure changes applied correctly
diff ${tmpd}/dir1 ${basedir}/dotfiles/${tmpd}/dir1
diff ${tmpd}/uniquefile ${basedir}/dotfiles/${tmpd}/uniquefile
[ ! -e ${basedir}/dotfiles/${tmpd}/dir1/sub1/sub2/sub3/file ] && echo "sub does not exist" && exit 1

## CLEANING
rm -rf ${basedir} ${tmpd}

echo "OK"
exit 0
