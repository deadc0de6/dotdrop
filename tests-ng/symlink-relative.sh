#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6
#
# test relative symlink
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
tmpw=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
export DOTDROP_WORKDIR="${tmpw}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpw}"

##################################################
# test symlink directory
##################################################
# create the file
echo "file1" > ${tmps}/dotfiles/abc
mkdir -p ${tmps}/dotfiles/def
echo 'file2' > ${tmps}/dotfiles/def/afile
echo '{{@@ header() @@}}' > ${tmps}/dotfiles/ghi
mkdir -p ${tmps}/dotfiles/jkl
echo '{{@@ header() @@}}' > ${tmps}/dotfiles/jkl/anotherfile

# create the config file
cfg="${tmps}/config.yaml"
cat > ${cfg} << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_dotfile_default: nolink
  workdir: ${tmpw}
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    link: relative
  f_abc2:
    dst: ${tmpd}/abc2
    src: abc
    link: absolute
  d_def:
    dst: ${tmpd}/def
    src: def
    link: relative
  f_ghi:
    dst: ${tmpd}/ghi
    src: ghi
    link: relative
  d_jkl:
    dst: ${tmpd}/jkl
    src: jkl
    link: relative
profiles:
  p1:
    dotfiles:
    - f_abc
    - f_abc2
    - d_def
    - f_ghi
    - d_jkl
_EOF
#cat ${cfg}

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

# ensure exists and is link
[ ! -h ${tmpd}/abc ] && echo "not a symlink" && exit 1
[ ! -h ${tmpd}/abc2 ] && echo "not a symlink" && exit 1
[ ! -h ${tmpd}/def ] && echo "not a symlink" && exit 1
[ ! -d ${tmpd}/def ] && echo "not a symlink" && exit 1
[ ! -h ${tmpd}/ghi ] && echo "not a symlink" && exit 1
[ ! -h ${tmpd}/jkl ] && echo "not a symlink" && exit 1
[ ! -d ${tmpd}/jkl ] && echo "not a symlink" && exit 1

ls -l ${tmpd}/abc | grep '\.\.' || exit 1
ls -l ${tmpd}/abc2
ls -l ${tmpd}/def | grep '\.\.' || exit 1
ls -l ${tmpd}/ghi | grep '\.\.' || exit 1
ls -l ${tmpd}/jkl | grep '\.\.' || exit 1

grep 'file1' ${tmpd}/abc
grep 'file1' ${tmpd}/abc2
grep 'file2' ${tmpd}/def/afile
grep 'This dotfile is managed using dotdrop' ${tmpd}/ghi
grep 'This dotfile is managed using dotdrop' ${tmpd}/jkl/anotherfile

[[ $(realpath --relative-base="${tmpw}" -- "$(realpath ${tmpd}/ghi)") =~ "^/" ]] && echo "ghi not subpath of workdir" && exit 1
[[ $(realpath --relative-base="${tmpw}" -- "$(realpath ${tmpd}/jkl)") =~ ^/ ]] && echo "jkl not subpath of workdir" && exit 1

## TODO test with install path children of dotpath
echo "TODO more tests"
exit 1

echo "OK"
exit 0
