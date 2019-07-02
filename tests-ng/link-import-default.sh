#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test the use of the keyword "link_on_import"
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

# create the config file
cfg="${tmps}/config.yaml"

# create the source
echo "abc" > ${tmpd}/abc

# import with nolink by default
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_on_import: nolink
dotfiles:
profiles:
_EOF

# import
cd ${ddpath} | ${bin} import -c ${cfg} -p p1 -V ${tmpd}/abc

# checks
inside="${tmps}/dotfiles/${tmpd}/abc"
[ ! -e ${inside} ] && exit 1

set +e
cat ${cfg} | grep 'link:' && exit 1
set -e

# import with parent by default
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_on_import: link
dotfiles:
profiles:
_EOF

# import
cd ${ddpath} | ${bin} import -c ${cfg} -p p1 -V ${tmpd}/abc

# checks
inside="${tmps}/dotfiles/${tmpd}/abc"
[ ! -e ${inside} ] && exit 1

cat ${cfg}
cat ${cfg} | grep 'link: link' >/dev/null

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
