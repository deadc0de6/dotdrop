#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2020, deadc0de6
#
# test chmod on import
# with files and directories
# with different link
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

# $1 file
chmod_to_umask()
{
  u=`umask`
  u=`echo ${u} | sed 's/^0*//'`
  if [ -d ${1} ]; then
    v=$((777 - u))
  else
    v=$((666 - u))
  fi
  chmod ${v} ${1}
}

# the dotfile source
tmps=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
mkdir -p ${tmps}/dotfiles
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the dotfiles
dnormal="${tmpd}/dir_normal"
mkdir -p ${dnormal}
echo "dir_normal/f1" > ${dnormal}/file1
echo "dir_normal/f2" > ${dnormal}/file2
chmod 777 ${dnormal}

dlink="${tmpd}/dir_link"
mkdir -p ${dlink}
echo "dir_link/f1" > ${dlink}/file1
echo "dir_link/f2" > ${dlink}/file2
chmod 777 ${dlink}

dlinkchildren="${tmpd}/dir_link_children"
mkdir -p ${dlinkchildren}
echo "dir_linkchildren/f1" > ${dlinkchildren}/file1
echo "dir_linkchildren/f2" > ${dlinkchildren}/file2
chmod 777 ${dlinkchildren}

fnormal="${tmpd}/filenormal"
echo "filenormal" > ${fnormal}
chmod 777 ${fnormal}

flink="${tmpd}/filelink"
echo "filelink" > ${flink}
chmod 777 ${flink}

toimport="${dnormal} ${dlink} ${dlinkchildren} ${fnormal} ${flink}"

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

# import without --preserve-mode
for i in ${toimport}; do
  cd ${ddpath} | ${bin} import -c ${cfg} -f -p p1 -V ${i}
done

cat ${cfg}

# list files
cd ${ddpath} | ${bin} detail -c ${cfg} -p p1 -V

tot=`echo ${toimport} | wc -w`
cnt=`cat ${cfg} | grep "chmod: '777'" | wc -l`
[ "${cnt}" != "${tot}" ] && echo "not all chmod inserted (1)" && exit 1

## with link
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF

# clean
rm -rf ${tmps}/dotfiles
mkdir -p ${tmps}/dotfiles

# import without --preserve-mode and link
for i in ${toimport}; do
  cd ${ddpath} | ${bin} import -c ${cfg} -l link -f -p p1 -V ${i}
done

cat ${cfg}

# list files
cd ${ddpath} | ${bin} detail -c ${cfg} -p p1 -V

tot=`echo ${toimport} | wc -w`
cnt=`cat ${cfg} | grep "chmod: '777'" | wc -l`
[ "${cnt}" != "${tot}" ] && echo "not all chmod inserted (2)" && exit 1

tot=`echo ${toimport} | wc -w`
cnt=`cat ${cfg} | grep 'link: link' | wc -l`
[ "${cnt}" != "${tot}" ] && echo "not all link inserted" && exit 1

## --preserve-mode
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF

# clean
rm -rf ${tmps}/dotfiles
mkdir -p ${tmps}/dotfiles

# import with --preserve-mode
for i in ${toimport}; do
  chmod_to_umask ${i}
  cd ${ddpath} | ${bin} import -c ${cfg} -m -f -p p1 -V ${i}
done

cat ${cfg}

# list files
cd ${ddpath} | ${bin} detail -c ${cfg} -p p1 -V

tot=`echo ${toimport} | wc -w`
cnt=`cat ${cfg} | grep "chmod: " | wc -l`
[ "${cnt}" != "${tot}" ] && echo "not all chmod inserted (3)" && exit 1

## import normal
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF

# clean
rm -rf ${tmps}/dotfiles
mkdir -p ${tmps}/dotfiles

# import without --preserve-mode
for i in ${toimport}; do
  chmod_to_umask ${i}
  cd ${ddpath} | ${bin} import -c ${cfg} -f -p p1 -V ${i}
done

cat ${cfg}

# list files
cd ${ddpath} | ${bin} detail -c ${cfg} -p p1 -V

cnt=`cat ${cfg} | grep chmod | wc -l`
[ "${cnt}" != "0" ] && echo "chmod inserted but not needed" && exit 1

## with config option chmod_on_import
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  chmod_on_import: true
dotfiles:
profiles:
_EOF

# clean
rm -rf ${tmps}/dotfiles
mkdir -p ${tmps}/dotfiles

# import
for i in ${toimport}; do
  chmod_to_umask ${i}
  cd ${ddpath} | ${bin} import -c ${cfg} -f -p p1 -V ${i}
done

cat ${cfg}

# list files
cd ${ddpath} | ${bin} detail -c ${cfg} -p p1 -V

cat ${cfg}
tot=`echo ${toimport} | wc -w`
cnt=`cat ${cfg} | grep "chmod: " | wc -l`
[ "${cnt}" != "${tot}" ] && echo "not all chmod inserted (3)" && exit 1

echo "OK"
exit 0
