#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test jinja2 filters from filter_file
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
#echo "dotfile destination: ${tmpd}"
filter_file=`mktemp`
filter_file2=`mktemp`
filter_file3=`mktemp`

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${filter_file}"
clear_on_exit "${filter_file2}"
clear_on_exit "${filter_file3}"

# create the config file
cfg="${tmps}/config.yaml"
cfgext="${tmps}/ext.yaml"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  filter_file:
  - ${filter_file}
  - ${filter_file2}
  import_configs:
  - ${cfgext}
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
variables:
  filt: "{{@@ 'whatever' | filter1 @@}}"
_EOF
#cat ${cfg}

cat > ${cfgext} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  filter_file:
  - ${filter_file3}
profiles:
dotfiles:
_EOF

cat << _EOF > ${filter_file}
def filter1(arg1):
  return "filtered"
def filter2(arg1, arg2=''):
  return arg2
_EOF

cat << _EOF > ${filter_file2}
def filter3(integer):
  return str(int(integer) - 10)
_EOF

cat << _EOF > ${filter_file3}
def filter_ext(arg1):
  return "external"
_EOF

# create the dotfile
echo "this is the test dotfile" > ${tmps}/dotfiles/abc

# test imported function
echo "{{@@ "abc" | filter1 @@}}" >> ${tmps}/dotfiles/abc
echo "{{@@ "arg1" | filter2('arg2') @@}}" >> ${tmps}/dotfiles/abc
echo "{{@@ "13" | filter3() @@}}" >> ${tmps}/dotfiles/abc
echo "{{@@ "something" | filter_ext() @@}}" >> ${tmps}/dotfiles/abc
echo "{{@@ filt @@}}variable" >> ${tmps}/dotfiles/abc

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

#cat ${tmpd}/abc

grep '^filtered$' ${tmpd}/abc >/dev/null
grep '^arg2$' ${tmpd}/abc >/dev/null
grep '^3$' ${tmpd}/abc >/dev/null
grep '^external$' ${tmpd}/abc >/dev/null
set +e
grep '^something$' ${tmpd}/abc >/dev/null && exit 1
set -e
grep '^filteredvariable$' ${tmpd}/abc > /dev/null

echo "OK"
exit 0
