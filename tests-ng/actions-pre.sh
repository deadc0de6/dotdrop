#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test pre action execution
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

# the action temp
tmpa=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
# the dotfile source
tmps=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
mkdir -p ${tmps}/dotfiles
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
actions:
  pre:
    failpre: "false"
    preaction: echo 'pre' > ${tmpa}/pre
    preaction2: echo 'pre2' > ${tmpa}/pre2
    preaction3: echo 'pre3' > ${tmpa}/pre3
    multiple: echo 'multiple' >> ${tmpa}/multiple
    multiple2: echo 'multiple2' >> ${tmpa}/multiple2
  nakedaction: echo 'naked' > ${tmpa}/naked
  nakedaction2: echo 'naked2' > ${tmpa}/naked2
  nakedaction3: echo 'naked3' > ${tmpa}/naked3
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    actions:
      - preaction
      - nakedaction
  f_fail:
    dst: ${tmpd}/fail
    src: fail
    actions:
      - failpre
  f_link:
    dst: ${tmpd}/link
    src: link
    link: true
    actions:
      - preaction2
      - nakedaction2
  d_dir:
    dst: ${tmpd}/dir
    src: dir
    actions:
      - multiple
  d_dlink:
    dst: ${tmpd}/dlink
    src: dlink
    link: true
    actions:
      - preaction3
      - nakedaction3
      - multiple2
profiles:
  p1:
    dotfiles:
    - f_abc
    - f_link
    - d_dir
    - d_dlink
  p2:
    dotfiles:
    - f_fail
_EOF
#cat ${cfg}

# create the dotfile
echo 'test' > ${tmps}/dotfiles/abc
echo 'link' > ${tmps}/dotfiles/link
echo 'fail' > ${tmps}/dotfiles/fail

mkdir -p ${tmps}/dotfiles/dir
echo 'test1' > ${tmps}/dotfiles/dir/file1
echo 'test2' > ${tmps}/dotfiles/dir/file2

mkdir -p ${tmps}/dotfiles/dlink
echo 'test3' > ${tmps}/dotfiles/dlink/dfile1
echo 'test4' > ${tmps}/dotfiles/dlink/dfile2

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

# checks
[ ! -e ${tmpa}/pre ] && echo 'pre action not executed' && exit 1
grep pre ${tmpa}/pre >/dev/null
[ ! -e ${tmpa}/naked ] && echo 'naked action not executed'  && exit 1
grep naked ${tmpa}/naked >/dev/null

[ ! -e ${tmpa}/multiple ] && echo 'pre action multiple not executed' && exit 1
grep multiple ${tmpa}/multiple >/dev/null
[ "`wc -l ${tmpa}/multiple | awk '{print $1}'`" -gt "1" ] && echo 'pre action multiple executed twice' && exit 1

[ ! -e ${tmpa}/pre2 ] && echo 'pre action 2 not executed' && exit 1
grep pre2 ${tmpa}/pre2 >/dev/null
[ ! -e ${tmpa}/naked2 ] && echo 'naked action 2 not executed'  && exit 1
grep naked2 ${tmpa}/naked2 >/dev/null

[ ! -e ${tmpa}/multiple2 ] && echo 'pre action multiple 2 not executed' && exit 1
grep multiple2 ${tmpa}/multiple2 >/dev/null
[ "`wc -l ${tmpa}/multiple2 | awk '{print $1}'`" -gt "1" ] && echo 'pre action multiple 2 executed twice' && exit 1
[ ! -e ${tmpa}/naked3 ] && echo 'naked action 3 not executed'  && exit 1
grep naked3 ${tmpa}/naked3 >/dev/null


# remove the pre action result and re-run
rm ${tmpa}/pre

cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1
[ -e ${tmpa}/pre ] && exit 1

# ensure failing actions make the installation fail
# install
set +e
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p2 -V
set -e
[ -e ${tmpd}/fail ] && exit 1

## CLEANING
rm -rf ${tmps} ${tmpd} ${tmpa}

echo "OK"
exit 0
