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
dt="${basedir}/dotfiles"
mkdir -p ${dt}/folder
touch ${dt}/folder/a

# the dotfile to be imported
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

# some files
cp -r ${dt}/folder ${tmpd}/
mkdir -p ${tmpd}/folder
touch ${tmpd}/folder/b
mkdir ${tmpd}/folder/c

# create the config file
cfg="${basedir}/config.yaml"
cat > ${cfg} << _EOF
config:
  backup: false
  create: true
  dotpath: dotfiles
dotfiles:
  thedotfile:
    dst: ${tmpd}/folder
    src: folder
profiles:
  p1:
    dotfiles:
    - thedotfile
_EOF

#
# Test with no ignore-missing setting
#

# Expect diff
echo "[+] test with no ignore-missing setting"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose --profile=p1
[ "$?" = "0" ] && exit 1
set -e

#
# Test with command-line flga
#

# Expect no diff
echo "[+] test with command-line flag"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose --profile=p1 --ignore-missing
[ "$?" != "0" ] && exit 1
set -e

#
# Test with global option
#

cat > ${cfg} << _EOF
config:
  backup: false
  create: true
  dotpath: dotfiles
  ignore_missing_in_dotdrop: true
dotfiles:
  thedotfile:
    dst: ${tmpd}/folder
    src: folder
profiles:
  p1:
    dotfiles:
    - thedotfile
_EOF

# Expect no diff
echo "[+] test global option"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose --profile=p1
[ "$?" != "0" ] && exit 1
set -e

#
# Test with dotfile option
#

cat > ${cfg} << _EOF
config:
  backup: false
  create: true
  dotpath: dotfiles
dotfiles:
  thedotfile:
    dst: ${tmpd}/folder
    src: folder
    ignore_missing_in_dotdrop: true
profiles:
  p1:
    dotfiles:
    - thedotfile
_EOF

# Expect no diff
echo "[+] test dotfile option"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose --profile=p1
[ "$?" != "0" ] && exit 1
set -e

echo "OK"
exit 0
