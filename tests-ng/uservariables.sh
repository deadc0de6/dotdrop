#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2021, deadc0de6
#
# test user variables from yaml file
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

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_variables:
    - uservariables.yaml:optional
variables:
  var4: "variables_var4"
dynvariables:
  var3: "echo dynvariables_var3"
uservariables:
  var1: "var1"
  var2: "var2"
  var3: "var3"
  var4: "var4"
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo "var1: {{@@ var1 @@}}" > ${tmps}/dotfiles/abc
echo "var2: {{@@ var2 @@}}" >> ${tmps}/dotfiles/abc
echo "var3: {{@@ var3 @@}}" >> ${tmps}/dotfiles/abc
echo "var4: {{@@ var4 @@}}" >> ${tmps}/dotfiles/abc

# install
echo "step 1"
cd ${ddpath} | echo -e 'var1contentxxx\nvar2contentyyy\nvar3\nvar4\n' | ${bin} install -f -c ${cfg} -p p1 -V

cat ${tmpd}/abc

grep '^var1: var1contentxxx$' ${tmpd}/abc >/dev/null
grep '^var2: var2contentyyy$' ${tmpd}/abc >/dev/null
grep '^var3: dynvariables_var3$' ${tmpd}/abc >/dev/null
grep '^var4: variables_var4$' ${tmpd}/abc >/dev/null

[ ! -e "${tmps}/uservariables.yaml" ] && exit 1

cat > "${tmps}/diff.yaml" << _EOF
variables:
  var1: var1contentxxx
  var2: var2contentyyy
_EOF
diff "${tmps}/diff.yaml" "${tmps}/uservariables.yaml"


cat > "${tmps}/uservariables.yaml" << _EOF
variables:
  var1: editedvar1
  var2: editedvar2
_EOF

echo "step 2"
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

grep '^var1: editedvar1$' ${tmpd}/abc >/dev/null
grep '^var2: editedvar2$' ${tmpd}/abc >/dev/null
grep '^var3: dynvariables_var3$' ${tmpd}/abc >/dev/null
grep '^var4: variables_var4$' ${tmpd}/abc >/dev/null

## CLEANING
rm -rf ${tmps} ${tmpd} ${scr}

echo "OK"
exit 0
