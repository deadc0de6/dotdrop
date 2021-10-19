#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2021, deadc0de6
#
# test compare dotfile from different profile
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
tmps=`mktemp -d --suffix='-dotdrop-tests-source' || mktemp -d`
dt="${tmps}/dotfiles"
mkdir -p ${dt}

xori="profile x"
xori="profile y"
echo "${xori}" > ${dt}/file_x
echo "${yori}" > ${dt}/file_y

# fs dotfiles
tmpd=`mktemp -d --suffix='-dotdrop-tests-dest' || mktemp -d`
touch ${tmpd}/file

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"
cat > ${cfg} << _EOF
config:
  backup: false
  create: true
  dotpath: dotfiles
dotfiles:
  f_file_x:
    dst: ${tmpd}/file
    src: file_x
  f_file_y:
    dst: ${tmpd}/file
    src: file_y
profiles:
  x:
    dotfiles:
    - f_file_x
  y:
    dotfiles:
    - f_file_y
_EOF
cat ${cfg}

# reset
echo "${xori}" > ${dt}/file_x
echo "${yori}" > ${dt}/file_y

echo "test compare profile x (ok)"
echo "${xori}" > ${tmpd}/file
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose -p x -C ${tmpd}/file
[ "$?" != "0" ] && exit 1
set -e

echo "test compare profile x (not ok)"
echo "${yori}" > ${tmpd}/file
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose -p x -C ${tmpd}/file
[ "$?" = "0" ] && exit 1
set -e

echo "test compare profile y (ok)"
echo "${yori}" > ${tmpd}/file
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose -p y -C ${tmpd}/file
[ "$?" != "0" ] && exit 1
set -e

echo "test compare profile y (not ok)"
echo "${xori}" > ${tmpd}/file
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose -p y -C ${tmpd}/file
[ "$?" = "0" ] && exit 1
set -e

echo "test compare profile x generic (ok)"
echo "${xori}" > ${tmpd}/file
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose -p x
[ "$?" != "0" ] && exit 1
set -e

echo "test compare profile x generic (not ok)"
echo "${yori}" > ${tmpd}/file
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose -p x
[ "$?" = "0" ] && exit 1
set -e

echo "test compare profile y generic (ok)"
echo "${yori}" > ${tmpd}/file
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose -p y
[ "$?" != "0" ] && exit 1
set -e

echo "test compare profile y generic (not ok)"
echo "${xori}" > ${tmpd}/file
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose -p y
[ "$?" = "0" ] && exit 1
set -e

echo "OK"
exit 0
