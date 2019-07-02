#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test the use of the keyword "include"
# that has to be ordered
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

# the dotfile source
tmps=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
mkdir -p ${tmps}/dotfiles
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
# temporary
tmpa=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
actions:
  pre:
    first: 'echo first > ${tmpa}/cookie'
    second: 'echo second >> ${tmpa}/cookie'
    third: 'echo third >> ${tmpa}/cookie'
dotfiles:
  f_first:
    dst: ${tmpd}/first
    src: first
    actions:
    - first
  f_second:
    dst: ${tmpd}/second
    src: second
    actions:
    - second
  f_third:
    dst: ${tmpd}/third
    src: third
    actions:
    - third
profiles:
  p0:
    dotfiles:
    - f_first
    include:
    - second
    - third
  second:
    dotfiles:
    - f_second
  third:
    dotfiles:
    - f_third
_EOF

# create the source
mkdir -p ${tmps}/dotfiles/
echo "first" > ${tmps}/dotfiles/first
echo "second" > ${tmps}/dotfiles/second
echo "third" > ${tmps}/dotfiles/third

attempts="3"
for ((i=0;i<${attempts};i++)); do
  # install
  cd ${ddpath} | ${bin} install -f -c ${cfg} -p p0 -V

  # checks timestamp
  echo "first timestamp: `stat -c %y ${tmpd}/first`"
  echo "second timestamp: `stat -c %y ${tmpd}/second`"
  echo "third timestamp: `stat -c %y ${tmpd}/third`"

  ts_first=`date "+%S%N" -d "$(stat -c %y ${tmpd}/first)"`
  ts_second=`date "+%S%N" -d "$(stat -c %y ${tmpd}/second)"`
  ts_third=`date "+%S%N" -d "$(stat -c %y ${tmpd}/third)"`

  #echo "first ts: ${ts_first}"
  #echo "second ts: ${ts_second}"
  #echo "third ts: ${ts_third}"

  [ "${ts_first}" -ge "${ts_second}" ] && echo "second created before first" && exit 1
  [ "${ts_second}" -ge "${ts_third}" ] && echo "third created before second" && exit 1

  # check cookie
  cat ${tmpa}/cookie
  content=`cat ${tmpa}/cookie | xargs`
  [ "${content}" != "first second third" ] && echo "bad cookie" && exit 1

  # clean
  rm ${tmpa}/cookie
  rm ${tmpd}/first ${tmpd}/second ${tmpd}/third
done

## CLEANING
rm -rf ${tmps} ${tmpd} ${tmpa}

echo "OK"
exit 0
