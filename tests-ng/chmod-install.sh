#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2020, deadc0de6
#
# test chmod on install
# with files and directories
# with different link
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

# $1 path
# $2 rights
has_rights()
{
  echo "testing ${1} is ${2}"
  [ ! -e "$1" ] && echo "`basename $1` does not exist" && exit 1
  local mode=`stat -L -c '%a' "$1"`
  [ "${mode}" != "$2" ] && echo "bad mode for `basename $1` (${mode} VS expected ${2})" && exit 1
  true
}

get_file_mode()
{
  u=`umask`
  u=`echo ${u} | sed 's/^0*//'`
  v=$((666 - u))
  echo "${v}"
}

get_dir_mode()
{
  u=`umask`
  u=`echo ${u} | sed 's/^0*//'`
  v=$((777 - u))
  echo "${v}"
}

# the dotfile source
tmps=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
mkdir -p ${tmps}/dotfiles
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
#echo "dotfile destination: ${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"

echo 'f777' > ${tmps}/dotfiles/f777
echo 'link' > ${tmps}/dotfiles/link
mkdir -p ${tmps}/dotfiles/dir
echo "f1" > ${tmps}/dotfiles/dir/f1

echo "exists" > ${tmps}/dotfiles/exists
chmod 644 ${tmps}/dotfiles/exists
echo "exists" > ${tmpd}/exists
chmod 644 ${tmpd}/exists

echo "existslink" > ${tmps}/dotfiles/existslink
chmod 644 ${tmpd}/exists

mkdir -p ${tmps}/dotfiles/direxists
echo "f1" > ${tmps}/dotfiles/direxists/f1
mkdir -p ${tmpd}/direxists
echo "f1" > ${tmpd}/direxists/f1
chmod 644 ${tmpd}/direxists/f1
chmod 744 ${tmpd}/direxists

mkdir -p ${tmps}/dotfiles/linkchildren
echo "f1" > ${tmps}/dotfiles/linkchildren/f1
mkdir -p ${tmps}/dotfiles/linkchildren/d1
echo "f2" > ${tmps}/dotfiles/linkchildren/d1/f2

echo '{{@@ profile @@}}' > ${tmps}/dotfiles/symlinktemplate

mkdir -p ${tmps}/dotfiles/symlinktemplatedir
echo "{{@@ profile @@}}" > ${tmps}/dotfiles/symlinktemplatedir/t

echo 'nomode' > ${tmps}/dotfiles/nomode

cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_f777:
    src: f777
    dst: ${tmpd}/f777
    chmod: 777
  f_link:
    src: link
    dst: ${tmpd}/link
    chmod: 777
    link: link
  d_dir:
    src: dir
    dst: ${tmpd}/dir
    chmod: 777
  f_exists:
    src: exists
    dst: ${tmpd}/exists
    chmod: 777
  f_existslink:
    src: existslink
    dst: ${tmpd}/existslink
    chmod: 777
    link: link
  d_direxists:
    src: direxists
    dst: ${tmpd}/direxists
    chmod: 777
  d_linkchildren:
    src: linkchildren
    dst: ${tmpd}/linkchildren
    chmod: 777
    link: link_children
  f_symlinktemplate:
    src: symlinktemplate
    dst: ${tmpd}/symlinktemplate
    chmod: 777
    link: link
  d_symlinktemplatedir:
    src: symlinktemplatedir
    dst: ${tmpd}/symlinktemplatedir
    chmod: 777
    link: link
  f_nomode:
    src: nomode
    dst: ${tmpd}/nomode
profiles:
  p1:
    dotfiles:
    - f_f777
    - f_link
    - d_dir
    - f_exists
    - f_existslink
    - d_direxists
    - d_linkchildren
    - f_symlinktemplate
    - d_symlinktemplatedir
    - f_nomode
  p2:
    dotfiles:
    - f_exists
    - f_existslink
    - d_linkchildren
    - f_symlinktemplate
    - f_nomode
_EOF
#cat ${cfg}

# install
echo "first install round"
cd ${ddpath} | ${bin} install -c ${cfg} -f -p p1 -V

has_rights "${tmpd}/f777" "777"
has_rights "${tmpd}/link" "777"
has_rights "${tmpd}/dir" "777"
has_rights "${tmpd}/exists" "777"
has_rights "${tmpd}/existslink" "777"
has_rights "${tmpd}/direxists" "777"
has_rights "${tmpd}/direxists/f1" "644"
has_rights "${tmpd}/linkchildren" "777"
has_rights "${tmpd}/linkchildren/f1" "644"
has_rights "${tmpd}/linkchildren/d1" "755"
has_rights "${tmpd}/linkchildren/d1/f2" "644"
has_rights "${tmpd}/symlinktemplate" "777"
m=`get_file_mode`
has_rights "${tmpd}/nomode" "${m}"

grep 'p1' ${tmpd}/symlinktemplate
grep 'p1' ${tmpd}/symlinktemplatedir/t

## second round
echo "exists" > ${tmps}/dotfiles/exists
chmod 600 ${tmps}/dotfiles/exists
echo "exists" > ${tmpd}/exists
chmod 600 ${tmpd}/exists

chmod 600 ${tmpd}/existslink

chmod 700 ${tmpd}/linkchildren

chmod 600 ${tmpd}/symlinktemplate

echo "second install round"
cd ${ddpath} | ${bin} install -c ${cfg} -p p2 -f -V

has_rights "${tmpd}/exists" "777"
has_rights "${tmpd}/existslink" "777"
has_rights "${tmpd}/linkchildren/f1" "644"
has_rights "${tmpd}/linkchildren/d1" "755"
has_rights "${tmpd}/linkchildren/d1/f2" "644"
has_rights "${tmpd}/symlinktemplate" "777"
m=`get_file_mode`
has_rights "${tmpd}/nomode" "${m}"

## no user confirmation expected
## same mode
echo "same mode"
echo "nomode" > ${tmps}/dotfiles/nomode
chmod 600 ${tmps}/dotfiles/nomode
echo "nomode" > ${tmpd}/nomode
chmod 600 ${tmpd}/nomode
cd ${ddpath} | ${bin} install -c ${cfg} -f -p p2 -V f_nomode
has_rights "${tmpd}/nomode" "600"

## no user confirmation with force
## different mode
echo "different mode"
echo "nomode" > ${tmps}/dotfiles/nomode
chmod 600 ${tmps}/dotfiles/nomode
echo "nomode" > ${tmpd}/nomode
chmod 700 ${tmpd}/nomode
cd ${ddpath} | ${bin} install -c ${cfg} -f -p p2 -V f_nomode
has_rights "${tmpd}/nomode" "600"

## user confirmation expected
## different mode
echo "different mode"
echo "nomode" > ${tmps}/dotfiles/nomode
chmod 600 ${tmps}/dotfiles/nomode
echo "nomode" > ${tmpd}/nomode
chmod 700 ${tmpd}/nomode
cd ${ddpath} | printf 'y\ny\n' | ${bin} install -f -c ${cfg} -p p2 -V f_nomode
has_rights "${tmpd}/nomode" "600"

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
