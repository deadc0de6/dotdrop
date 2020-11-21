#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# the only purpose is to test corner-cases
# not covered by other tests like
# dry
# diff before write
# etc
#
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
basedir=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"

export DOTDROP_WORKERS=1

# create the config file
cfg="${basedir}/config.yaml"
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_x:
    src: /tmp/x
    dst:
  f_y:
    src: /tmp/.i-do-not-exist-dotdrop
    dst: /tmp/y
profiles:
  p1:
    dotfiles:
    - f_x
    - f_y

_EOF

echo "[+] test install dry"
cd ${ddpath} | ${bin} install -c ${cfg} --dry -p p1 --verbose f_x
[ "$?" != "0" ] && exit 1

echo "[+] test install show-diff"
cd ${ddpath} | ${bin} install -c ${cfg} -p p1 --verbose f_x
[ "$?" != "0" ] && exit 1
cd ${ddpath} | ${bin} install -D -c ${cfg} -p p1 --verbose f_x
[ "$?" != "0" ] && exit 1

echo "[+] test install not existing src"
cd ${ddpath} | ${bin} install -c ${cfg} -f --dry -p p1 --verbose f_y

echo "[+] test install to temp"
cd ${ddpath} | ${bin} install -t -c ${cfg} -p p1 --verbose f_x
[ "$?" != "0" ] && exit 1

## CLEANING
rm -rf ${basedir}

echo "OK"
exit 0
