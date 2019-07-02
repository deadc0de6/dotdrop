#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test the behavior when playing with link_dotfile_default
# and link_on_import on import
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

# ----------------------------------------------------------
echo -e "\n======> import with all default"
# create the source
rm -rf ${tmpd}/qwert
echo "test" > ${tmpd}/qwert
# clean
rm -rf ${tmps}/dotfiles
mkdir -p ${tmps}/dotfiles
# config file
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF

# import
df="${tmpd}/qwert"
cd ${ddpath} | ${bin} import -c ${cfg} -p p1 ${df} -V

# checks
cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V
line=$(cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V | grep "f_`basename ${df}`")
echo ${line} | grep 'link: nolink'

# try to install
rm -rf ${tmpd}/qwert
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V
[ ! -e ${df} ] && echo "does not exist" && exit 1
[ -h ${df} ] && echo "is symlink" && exit 1

# ----------------------------------------------------------
echo -e "\n======> import with link_on_import=nolink and link_dotfile_default=nolink"
# create the source
rm -rf ${tmpd}/qwert
echo "test" > ${tmpd}/qwert
# clean
rm -rf ${tmps}/dotfiles
mkdir -p ${tmps}/dotfiles
# config file
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_on_import: nolink
  link_dotfile_default: nolink
dotfiles:
profiles:
_EOF

# import
df="${tmpd}/qwert"
cd ${ddpath} | ${bin} import -c ${cfg} -p p1 ${df} -V

# checks
cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V
line=$(cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V | grep "f_`basename ${df}`")
echo ${line} | grep 'link: nolink'

# try to install
rm -rf ${tmpd}/qwert
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V
[ ! -e ${df} ] && echo "does not exist" && exit 1
[ -h ${df} ] && echo "is symlink" && exit 1

# ----------------------------------------------------------
echo -e "\n======> import with link_on_import=nolink and link_dotfile_default=nolink and --link=nolink"
# create the source
rm -rf ${tmpd}/qwert
echo "test" > ${tmpd}/qwert
# clean
rm -rf ${tmps}/dotfiles
mkdir -p ${tmps}/dotfiles
# config file
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_on_import: nolink
  link_dotfile_default: nolink
dotfiles:
profiles:
_EOF

# import
df="${tmpd}/qwert"
cd ${ddpath} | ${bin} import -c ${cfg} -p p1 ${df} -V --link=nolink

# checks
cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V
line=$(cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V | grep "f_`basename ${df}`")
echo ${line} | grep 'link: nolink'

# try to install
rm -rf ${tmpd}/qwert
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V
[ ! -e ${df} ] && echo "does not exist" && exit 1
[ -h ${df} ] && echo "is symlink" && exit 1

# ----------------------------------------------------------
echo -e "\n======> import with link_on_import=nolink and link_dotfile_default=nolink and --link=link"
# create the source
rm -rf ${tmpd}/qwert
echo "test" > ${tmpd}/qwert
# clean
rm -rf ${tmps}/dotfiles
mkdir -p ${tmps}/dotfiles
# config file
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_on_import: nolink
  link_dotfile_default: nolink
dotfiles:
profiles:
_EOF

# import
df="${tmpd}/qwert"
cd ${ddpath} | ${bin} import -c ${cfg} -p p1 ${df} -V --link=link

# checks
cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V
line=$(cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V | grep "f_`basename ${df}`")
echo ${line} | grep 'link: link'

# try to install
rm -rf ${tmpd}/qwert
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V
[ ! -e ${df} ] && echo "does not exist" && exit 1
[ ! -h ${df} ] && echo "not symlink" && exit 1

# ----------------------------------------------------------
echo -e "\n======> import with link_on_import=link and link_dotfile_default=nolink"
# create the source
rm -rf ${tmpd}/qwert
echo "test" > ${tmpd}/qwert
# clean
rm -rf ${tmps}/dotfiles
mkdir -p ${tmps}/dotfiles
# config file
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_on_import: link
  link_dotfile_default: nolink
dotfiles:
profiles:
_EOF

# import
df="${tmpd}/qwert"
cd ${ddpath} | ${bin} import -c ${cfg} -p p1 ${df} -V

# checks
cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V
line=$(cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V | grep "f_`basename ${df}`")
echo ${line} | grep 'link: link'

# try to install
rm -rf ${tmpd}/qwert
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V
[ ! -e ${df} ] && echo "does not exist" && exit 1
[ ! -h ${df} ] && echo "not symlink" && exit 1

# ----------------------------------------------------------
echo -e "\n======> import with link_on_import=link and link_dotfile_default=nolink and --link=nolink"
# create the source
rm -rf ${tmpd}/qwert
echo "test" > ${tmpd}/qwert
# clean
rm -rf ${tmps}/dotfiles
mkdir -p ${tmps}/dotfiles
# config file
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_on_import: link
  link_dotfile_default: nolink
dotfiles:
profiles:
_EOF

# import
df="${tmpd}/qwert"
cd ${ddpath} | ${bin} import -c ${cfg} -p p1 ${df} -V --link=nolink

# checks
cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V
line=$(cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V | grep "f_`basename ${df}`")
echo ${line} | grep 'link: nolink'

# try to install
rm -rf ${tmpd}/qwert
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V
[ ! -e ${df} ] && echo "does not exist" && exit 1
[ -h ${df} ] && echo "is symlink" && exit 1

# ----------------------------------------------------------
echo -e "\n======> import with link_on_import=nolink and link_dotfile_default=link"
# create the source
rm -rf ${tmpd}/qwert
echo "test" > ${tmpd}/qwert
# clean
rm -rf ${tmps}/dotfiles
mkdir -p ${tmps}/dotfiles
# config file
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_on_import: nolink
  link_dotfile_default: link
dotfiles:
profiles:
_EOF

# import
df="${tmpd}/qwert"
cd ${ddpath} | ${bin} import -c ${cfg} -p p1 ${df} -V --link=nolink

# checks
cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V
line=$(cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V | grep "f_`basename ${df}`")
echo ${line} | grep 'link: nolink'

# try to install
rm -rf ${tmpd}/qwert
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V
[ ! -e ${df} ] && echo "does not exist" && exit 1
[ -h ${df} ] && echo "is symlink" && exit 1

# ----------------------------------------------------------
echo -e "\n======> import with link_on_import=link and link_dotfile_default=nolink and --link=nolink"
# create the source
rm -rf ${tmpd}/qwert
echo "test" > ${tmpd}/qwert
# clean
rm -rf ${tmps}/dotfiles
mkdir -p ${tmps}/dotfiles
# config file
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_on_import: link
  link_dotfile_default: nolink
dotfiles:
profiles:
_EOF

# import
df="${tmpd}/qwert"
cd ${ddpath} | ${bin} import -c ${cfg} -p p1 ${df} -V --link=nolink

# checks
cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V
line=$(cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V | grep "f_`basename ${df}`")
echo ${line} | grep 'link: nolink'

# try to install
rm -rf ${tmpd}/qwert
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V
[ ! -e ${df} ] && echo "does not exist" && exit 1
[ -h ${df} ] && echo "is symlink" && exit 1

# ----------------------------------------------------------
echo -e "\n======> import with all default and --link=link"
# create the source
rm -rf ${tmpd}/qwert
echo "test" > ${tmpd}/qwert
# clean
rm -rf ${tmps}/dotfiles
mkdir -p ${tmps}/dotfiles
# config file
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF

# import
df="${tmpd}/qwert"
cd ${ddpath} | ${bin} import -c ${cfg} --link=link -p p1 ${df} -V

# checks
cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V
line=$(cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V | grep "f_`basename ${df}`")
echo ${line} | grep 'link: link'

# try to install
rm -rf ${tmpd}/qwert
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V
[ ! -e ${df} ] && echo "does not exist" && exit 1
[ ! -h ${df} ] && echo "not a symlink" && exit 1

# ----------------------------------------------------------
echo -e "\n======> import with all default and --link=link_children"
# create the source
rm -rf ${tmpd}/qwert
echo "test" > ${tmpd}/qwert
# clean
rm -rf ${tmps}/dotfiles
mkdir -p ${tmps}/dotfiles
# config file
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF

# import
df="${tmpd}/qwert"
set +e
cd ${ddpath} | ${bin} import -c ${cfg} --link=link_children -p p1 ${df} -V
[ "$?" = "0" ] && echo "link_children with file should fail" && exit 1
set -e

# ----------------------------------------------------------
echo -e "\n======> import with all default and --link=link_children"
# create the source
rm -rf ${tmpd}/qwert
mkdir -p ${tmpd}/qwert
echo "test" > ${tmpd}/qwert/file
mkdir -p ${tmpd}/qwert/directory
echo "test" > ${tmpd}/qwert/directory/file

# clean
rm -rf ${tmps}/dotfiles
mkdir -p ${tmps}/dotfiles
# config file
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF

# import
df="${tmpd}/qwert"
cd ${ddpath} | ${bin} import -c ${cfg} --link=link_children -p p1 ${df} -V

# checks
cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V
line=$(cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V | grep "d_`basename ${df}`")
echo ${line} | grep 'link: link_children'

# try to install
rm -rf ${tmpd}/qwert
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V
[ ! -e ${df} ] && echo "does not exist" && exit 1
[ -h ${df} ] && echo "is a symlink" && exit 1
[ ! -h ${df}/file ] && echo "file is not a symlink" && exit 1
[ ! -h ${df}/directory ] && echo "directory is not a symlink" && exit 1
[ -h ${df}/directory/file ] && echo "directory/file is a symlink" && exit 1

echo -e "\n======> import with link_on_import=link_children and link_dotfile_default=nolink"
# create the source
rm -rf ${tmpd}/qwert
mkdir -p ${tmpd}/qwert
echo "test" > ${tmpd}/qwert/file
mkdir -p ${tmpd}/qwert/directory
echo "test" > ${tmpd}/qwert/directory/file

# clean
rm -rf ${tmps}/dotfiles
mkdir -p ${tmps}/dotfiles
# config file
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_on_import: link_children
  link_dotfile_default: nolink
dotfiles:
profiles:
_EOF

# import
df="${tmpd}/qwert"
cd ${ddpath} | ${bin} import -c ${cfg} -p p1 ${df} -V

# checks
cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V
line=$(cd ${ddpath} | ${bin} listfiles -c ${cfg} -p p1 -V | grep "d_`basename ${df}`")
echo ${line} | grep 'link: link_children'

# try to install
rm -rf ${tmpd}/qwert
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V
[ ! -e ${df} ] && echo "does not exist" && exit 1
[ -h ${df} ] && echo "is a symlink" && exit 1
[ ! -h ${df}/file ] && echo "file is not a symlink" && exit 1
[ ! -h ${df}/directory ] && echo "directory is not a symlink" && exit 1
[ -h ${df}/directory/file ] && echo "directory/file is a symlink" && exit 1

## CLEANING
rm -rf ${tmps} ${tmpd}

echo "OK"
exit 0
