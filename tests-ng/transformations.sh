#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test transformations
# for install and compare
# returns 1 in case of error
#

# exit on first error
set -e
#set -v

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

# the dotfile source
tmps=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
mkdir -p ${tmps}/dotfiles
echo "dotfiles source (dotpath): ${tmps}"
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
echo "dotfiles destination: ${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"

# token
token="test-base64"
tokend="compressed archive"
touched="touched"

cat > ${cfg} << _EOF
trans:
  base64: cat {0} | base64 -d > {1}
  uncompress: mkdir -p {1} && tar -xf {0} -C {1}
trans_write:
  base64: cat {0} | base64 > {1}
  compress: tar -cf {1} -C {0} .
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_def:
    dst: ${tmpd}/def
    src: def
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    trans: base64
    trans_write: base64
  d_ghi:
    dst: ${tmpd}/ghi
    src: ghi
    trans: uncompress
    trans_write: compress
profiles:
  p1:
    dotfiles:
    - f_abc
    - f_def
    - d_ghi
_EOF
#cat ${cfg}

# create the base64 dotfile
tmpf=`mktemp --suffix='-dotdrop-tests' || mktemp -d`
echo ${token} > ${tmpf}
cat ${tmpf} | base64 > ${tmps}/dotfiles/abc
rm -f ${tmpf}

# create the canary dotfile
echo 'marker' > ${tmps}/dotfiles/def

# create the compressed dotfile
tmpx=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
mkdir -p ${tmpx}/{a,b,c}
mkdir -p ${tmpx}/a/{dir1,dir2}
# ambiguous redirect ??
#echo ${tokend} > ${tmpd}/{a,b,c}/somefile
echo ${tokend} > ${tmpx}/a/somefile
echo ${tokend} > ${tmpx}/b/somefile
echo ${tokend} > ${tmpx}/c/somefile
echo ${tokend} > ${tmpx}/a/dir1/otherfile
tar -cf ${tmps}/dotfiles/ghi -C ${tmpx} .
rm -rf ${tmpx}
tar -tf ${tmps}/dotfiles/ghi

###########################
# test install and compare
###########################

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -b -V

# check canary dotfile
[ ! -e ${tmpd}/def ] && exit 1

# check base64 dotfile
[ ! -e ${tmpd}/abc ] && exit 1
content=`cat ${tmpd}/abc`
[ "${content}" != "${token}" ] && exit 1

# check directory dotfile
[ ! -e ${tmpd}/ghi/a/dir1/otherfile ] && exit 1
content=`cat ${tmpd}/ghi/a/somefile`
[ "${content}" != "${tokend}" ] && exit 1
content=`cat ${tmpd}/ghi/a/dir1/otherfile`
[ "${content}" != "${tokend}" ] && exit 1

# compare
cd ${ddpath} | ${bin} compare -c ${cfg} -p p1 -b -V
[ "$?" != "0" ] && exit 1

# change base64 deployed file
echo ${touched} > ${tmpd}/abc
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} -p p1 -b -V
[ "$?" != "1" ] && exit 1
set -e

# change uncompressed deployed dotfile
echo ${touched} > ${tmpd}/ghi/a/somefile
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} -p p1 -b -V
[ "$?" != "1" ] && exit 1
set -e

###########################
# test update
###########################

# update single file
echo 'update' > ${tmpd}/def
cd ${ddpath} | ${bin} update -f -k -c ${cfg} -p p1 -b -V f_def
[ "$?" != "0" ] && exit 1
[ ! -e  ${tmpd}/def ] && echo 'dotfile in FS removed' && exit 1
[ ! -e  ${tmps}/dotfiles/def ] && echo 'dotfile in dotpath removed' && exit 1

# update single file
cd ${ddpath} | ${bin} update -f -k -c ${cfg} -p p1 -b -V f_abc
[ "$?" != "0" ] && exit 1

# test updated file
[ ! -e ${tmps}/dotfiles/abc ] && exit 1
content=`cat ${tmps}/dotfiles/abc`
bcontent=`echo ${touched} | base64`
[ "${content}" != "${bcontent}" ] && exit 1

# update directory
echo ${touched} > ${tmpd}/ghi/b/newfile
rm -r ${tmpd}/ghi/c
cd ${ddpath} | ${bin} update -f -k -c ${cfg} -p p1 -b -V d_ghi
[ "$?" != "0" ] && exit 1

# test updated directory
tar -tf ${tmps}/dotfiles/ghi | grep './b/newfile'
tar -tf ${tmps}/dotfiles/ghi | grep './a/dir1/otherfile'

tmpy=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
tar -xf ${tmps}/dotfiles/ghi -C ${tmpy}
content=`cat ${tmpy}/a/somefile`
[ "${content}" != "${touched}" ] && exit 1

# check canary dotfile
[ ! -e ${tmps}/dotfiles/def ] && exit 1

## CLEANING
rm -rf ${tmps} ${tmpd} ${tmpx} ${tmpy}

echo "OK"
exit 0
