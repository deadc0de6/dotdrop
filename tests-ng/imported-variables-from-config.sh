#!/usr/bin/env bash
# author: davla (https://github.com/davls)
# Copyright (c) 2020, davla
#
# test variables imported from config and used in the importing yaml config
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

# the dotfile source
tmps=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
mkdir -p ${tmps}/dotfiles
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"
subcfg="${tmps}/subconfig.yaml"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_configs:
  - ${subcfg}
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: '{{@@ abc_dyn_src @@}}{{@@ abc_src @@}}'
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
cat ${cfg}

# create the subconfig file
cat > ${subcfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
variables:
  abc_src: c
dynvariables:
  abc_dyn_src: 'echo ab'
dotfiles: []
profiles: []
_EOF

# create the dotfile
dirname ${tmps}/dotfiles/abc | xargs mkdir -p
cat > ${tmps}/dotfiles/abc << _EOF
Hell yeah
_EOF

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

# test file existence and content
[ -f "${tmpd}/abc" ] || {
    echo 'Dotfile not installed'
    exit 1
}

echo "OK"
exit 0
