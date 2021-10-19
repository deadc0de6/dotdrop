#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2020, deadc0de6
#
# test dry
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
# the dotfile source
tmps=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
mkdir -p ${tmps}/dotfiles
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
#echo "dotfile destination: ${tmpd}"
# workdir
tmpw=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
# temp
tmpa=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpw}"
clear_on_exit "${tmpa}"

# -----------------------------
# test install
# -----------------------------
# cleaning
rm -rf ${tmps}/*
mkdir -p ${tmps}/dotfiles
rm -rf ${tmpw}/*
rm -rf ${tmpd}/*
rm -rf ${tmpa}/*
# create the config file
cfg="${tmps}/config.yaml"

echo '{{@@ profile @@}}' > ${tmps}/dotfiles/file
echo '{{@@ profile @@}}' > ${tmps}/dotfiles/link
mkdir -p ${tmps}/dotfiles/dir
echo "{{@@ profile @@}}" > ${tmps}/dotfiles/dir/f1
mkdir -p ${tmps}/dotfiles/dirchildren
echo "{{@@ profile @@}}" > ${tmps}/dotfiles/dirchildren/f1
echo "{{@@ profile @@}}" > ${tmps}/dotfiles/dirchildren/f2

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  workdir: ${tmpw}
actions:
  pre:
    preaction: echo 'pre' > ${tmpa}/pre
  post:
    postaction: echo 'post' > ${tmpa}/post
dotfiles:
  f_file:
    src: file
    dst: ${tmpd}/file
    actions:
      - preaction
      - postaction
  f_link:
    src: link
    dst: ${tmpd}/link
    link: link
    actions:
      - preaction
      - postaction
  d_dir:
    src: dir
    dst: ${tmpd}/dir
    actions:
      - preaction
      - postaction
  d_dirchildren:
    src: dirchildren
    dst: ${tmpd}/dirchildren
    link: link_children
    actions:
      - preaction
      - postaction
profiles:
  p1:
    dotfiles:
    - f_file
    - f_link
    - d_dir
    - d_dirchildren
_EOF

# install
echo "dry install"
cd ${ddpath} | ${bin} install -c ${cfg} -f -p p1 -V --dry

cnt=`ls -1 ${tmpd} | wc -l`
ls -1 ${tmpd}
[ "${cnt}" != "0" ] && echo "dry install failed (1)" && exit 1

cnt=`ls -1 ${tmpw} | wc -l`
ls -1 ${tmpw}
[ "${cnt}" != "0" ] && echo "dry install failed (2)" && exit 1

cnt=`ls -1 ${tmpa} | wc -l`
ls -1 ${tmpa}
[ "${cnt}" != "0" ] && echo "dry install failed (3)" && exit 1

# -----------------------------
# test import
# -----------------------------
# cleaning
rm -rf ${tmps}/*
mkdir -p ${tmps}/dotfiles
rm -rf ${tmpw}/*
rm -rf ${tmpd}/*
rm -rf ${tmpa}/*

# create the config file
cfg="${tmps}/config.yaml"
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  workdir: ${tmpw}
dotfiles:
profiles:
_EOF
cp ${cfg} ${tmpa}/config.yaml

echo 'content' > ${tmpd}/file
echo 'content' > ${tmpd}/link
mkdir -p ${tmpd}/dir
echo "content" > ${tmpd}/dir/f1
mkdir -p ${tmpd}/dirchildren
echo "content" > ${tmpd}/dirchildren/f1
echo "content" > ${tmpd}/dirchildren/f2

dotfiles="${tmpd}/file ${tmpd}/link ${tmpd}/dir ${tmpd}/dirchildren"

echo "dry import"
cd ${ddpath} | ${bin} import -c ${cfg} -f -p p1 -V --dry ${dotfiles}

cnt=`ls -1 ${tmps}/dotfiles | wc -l`
ls -1 ${tmps}/dotfiles
[ "${cnt}" != "0" ] && echo "dry import failed (1)" && exit 1

diff ${cfg} ${tmpa}/config.yaml || (echo "dry import failed (2)" && exit 1)

# -----------------------------
# test update
# -----------------------------
# cleaning
rm -rf ${tmps}/*
mkdir -p ${tmps}/dotfiles
rm -rf ${tmpw}/*
rm -rf ${tmpd}/*
rm -rf ${tmpa}/*

echo 'original' > ${tmps}/dotfiles/file
echo 'original' > ${tmps}/dotfiles/link
mkdir -p ${tmps}/dotfiles/dir
echo "original" > ${tmps}/dotfiles/dir/f1
mkdir -p ${tmps}/dotfiles/dirchildren
echo "original" > ${tmps}/dotfiles/dirchildren/f1
echo "original" > ${tmps}/dotfiles/dirchildren/f2

echo 'modified' > ${tmpd}/file
echo 'modified' > ${tmpd}/link
mkdir -p ${tmpd}/dir
echo "modified" > ${tmpd}/dir/f1
mkdir -p ${tmpd}/dirchildren
echo "modified" > ${tmpd}/dirchildren/f1
echo "modified" > ${tmpd}/dirchildren/f2

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  workdir: ${tmpw}
dotfiles:
  f_file:
    src: file
    dst: ${tmpd}/file
  f_link:
    src: link
    dst: ${tmpd}/link
    link: link
  d_dir:
    src: dir
    dst: ${tmpd}/dir
  d_dirchildren:
    src: dirchildren
    dst: ${tmpd}/dirchildren
    link: link_children
profiles:
  p1:
    dotfiles:
    - f_file
    - f_link
    - d_dir
    - d_dirchildren
_EOF
cp ${cfg} ${tmpa}/config.yaml

echo "dry update"
dotfiles="${tmpd}/file ${tmpd}/link ${tmpd}/dir ${tmpd}/dirchildren"
cd ${ddpath} | ${bin} update -c ${cfg} -f -p p1 -V --dry ${dotfiles}

grep 'modified' ${tmps}/dotfiles/file   && echo "dry update failed (1)" && exit 1
grep 'modified' ${tmps}/dotfiles/link   && echo "dry update failed (2)" && exit 1
grep "modified" ${tmps}/dotfiles/dir/f1 && echo "dry update failed (3)" && exit 1
grep "modified" ${tmps}/dotfiles/dirchildren/f1 && echo "dry update failed (4)" && exit 1
grep "modified" ${tmps}/dotfiles/dirchildren/f2 && echo "dry update failed (5)" && exit 1

diff ${cfg} ${tmpa}/config.yaml || (echo "dry update failed (6)" && exit 1)

# -----------------------------
# test remove
# -----------------------------
# cleaning
rm -rf ${tmps}/*
mkdir -p ${tmps}/dotfiles
rm -rf ${tmpw}/*
rm -rf ${tmpd}/*
rm -rf ${tmpa}/*

echo '{{@@ profile @@}}' > ${tmps}/dotfiles/file
echo '{{@@ profile @@}}' > ${tmps}/dotfiles/link
mkdir -p ${tmps}/dotfiles/dir
echo "{{@@ profile @@}}" > ${tmps}/dotfiles/dir/f1
mkdir -p ${tmps}/dotfiles/dirchildren
echo "{{@@ profile @@}}" > ${tmps}/dotfiles/dirchildren/f1
echo "{{@@ profile @@}}" > ${tmps}/dotfiles/dirchildren/f2

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  workdir: ${tmpw}
dotfiles:
  f_file:
    src: file
    dst: ${tmpd}/file
  f_link:
    src: link
    dst: ${tmpd}/link
    link: link
  d_dir:
    src: dir
    dst: ${tmpd}/dir
  d_dirchildren:
    src: dirchildren
    dst: ${tmpd}/dirchildren
    link: link_children
profiles:
  p1:
    dotfiles:
    - f_file
    - f_link
    - d_dir
    - d_dirchildren
_EOF
cp ${cfg} ${tmpa}/config.yaml

echo "dry remove"
dotfiles="${tmpd}/file ${tmpd}/link ${tmpd}/dir ${tmpd}/dirchildren"
cd ${ddpath} | ${bin} remove -c ${cfg} -f -p p1 -V --dry ${dotfiles}

[ ! -e ${tmps}/dotfiles/file ] && echo "dry remove failed (1)" && exit 1
[ ! -e ${tmps}/dotfiles/link ] && echo "dry remove failed (2)" && exit 1
[ ! -d ${tmps}/dotfiles/dir ] && echo "dry remove failed (3)" && exit 1
[ ! -e ${tmps}/dotfiles/dir/f1 ] && echo "dry remove failed (4)" && exit 1
[ ! -d ${tmps}/dotfiles/dirchildren ] && echo "dry remove failed (5)" && exit 1
[ ! -e ${tmps}/dotfiles/dirchildren/f1 ] && echo "dry remove failed (6)" && exit 1
[ ! -e ${tmps}/dotfiles/dirchildren/f2 ] && echo "dry remove failed (7)" && exit 1

diff ${cfg} ${tmpa}/config.yaml || (echo "dry remove failed (8)" && exit 1)

echo "OK"
exit 0
