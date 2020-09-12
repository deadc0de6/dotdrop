#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test diff cmd
# returns 1 in case of error
#

# exit on first error
#set -e

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

# the dotfile to be imported
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`

# some files
echo "original" > ${tmpd}/singlefile

# create the config file
cfg="${basedir}/config.yaml"
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF

export DOTDROP_FORCE_NODEBUG=yes
export DOTDROP_NOBANNER=yes

# import
echo "[+] import"
cd ${ddpath} | ${bin} import -c ${cfg} ${tmpd}/singlefile

# modify the file
echo "modified" > ${tmpd}/singlefile

# default diff (unified)
echo "[+] comparing with default diff (unified)"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} 2>&1 | grep -v '=>' | grep -v '^+++\|^---' > ${tmpd}/normal
diff -u -r ${tmpd}/singlefile ${basedir}/dotfiles/${tmpd}/singlefile | grep -v '^+++\|^---' > ${tmpd}/real
set -e

# verify
diff ${tmpd}/normal ${tmpd}/real || exit 1

# adding normal diff
cfg2="${basedir}/config2.yaml"
sed '/dotpath: dotfiles/a \ \ diff_command: "diff -r {0} {1}"' ${cfg} > ${cfg2}
#cat ${cfg2}

# normal diff
echo "[+] comparing with normal diff"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg2} 2>&1 | grep -v '=>' > ${tmpd}/unified
diff -r ${tmpd}/singlefile ${basedir}/dotfiles/${tmpd}/singlefile > ${tmpd}/real
set -e

# verify
#cat ${tmpd}/unified
#cat ${tmpd}/real
diff ${tmpd}/unified ${tmpd}/real || exit 1

# adding fake diff
cfg3="${basedir}/config3.yaml"
sed '/dotpath: dotfiles/a \ \ diff_command: "echo fakediff"' ${cfg} > ${cfg3}
#cat ${cfg3}

# fake diff
echo "[+] comparing with fake diff"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg3} 2>&1 | grep -v '=>' > ${tmpd}/fake
set -e

# verify
#cat ${tmpd}/fake
grep fakediff ${tmpd}/fake &> /dev/null || exit 1

## CLEANING
rm -rf ${basedir} ${tmpd}

unset DOTDROP_NOBANNER
unset DOTDROP_FORCE_NODEBUG

echo "OK"
exit 0
