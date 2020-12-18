#!/usr/bin/env bash
# author: jtt9340 (https://github.com/jtt9340)
#
# test negative ignore update
# returns 1 in case of error
#

# exit on first error
set -e

# all this crap to get current path
if [ $(uname) = Darwin ]; then
  # Unfortunately, readlink works differently on macOS than it does on GNU/Linux
  # (the -f option behaves differently) and the realpath command does not exist.
  # Workarounds I find on the Internet suggest just using Homebrew to install coreutils
  # so you can get the GNU coreutils on your Mac. But, I don't want this script to
  # assume (a) users have Homebrew installed and (b) if they have Homebrew installed, that
  # they then installed the GNU coreutils.
  readlink() {
    TARGET_FILE=$1

    cd `dirname $TARGET_FILE`
    TARGET_FILE=`basename $TARGET_FILE`

    # Iterate down a (possible) chain of symlinks
    while [ -L "$TARGET_FILE" ]; do
      TARGET_FILE=`readlink $TARGET_FILE`
      cd `dirname $TARGET_FILE`
      TARGET_FILE=`basename $TARGET_FILE`
    done

    # Compute the canonicalized name by finding the physical path
    # for the directory we're in and appending the target file.
    PHYS_DIR=`pwd -P`
    RESULT=$PHYS_DIR/$TARGET_FILE
    echo $RESULT
  }
  rl="readlink"
else
  rl="readlink -f"
  if ! ${rl} "${0}" >/dev/null 2>&1; then
    rl="realpath"

    if ! hash ${rl}; then
      echo "\"${rl}\" not found !" && exit 1
    fi
  fi
fi
cur=$(dirname "$(${rl} "${0}")")

#hash dotdrop >/dev/null 2>&1
#[ "$?" != "0" ] && echo "install dotdrop to run tests" && exit 1

#echo "called with ${1}"

# dotdrop can be pass as argument
ddpath="${cur}/../"
[ "${1}" != "" ] && ddpath="${1}"
[ ! -d ${ddpath} ] && exho "ddpath \"${ddpath}\" is not a directory" && exit 1

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
basedir=`mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d`
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"
mkdir -p ${basedir}/dotfiles/a/{b,c}
echo 'a' > ${basedir}/dotfiles/a/b/abfile
echo 'a' > ${basedir}/dotfiles/a/c/acfile

# the dotfile to be updated
tmpd=`mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d`
cp -r ${basedir}/dotfiles/a ${tmpd}/

# create the config file
cfg="${basedir}/config.yaml"
cat > ${cfg} << _EOF
config:
  backup: false
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/a
    src: a
    upignore:
    - "*/newdir/b/*"
    - "!*/newdir/b/d"
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# edit/add files
echo "[+] edit/add files"
mkdir -p ${tmpd}/a/newdir/b
touch ${tmpd}/a/newdir/b/{c,d}

# update
echo "[+] update"
cd ${ddpath} | ${bin} update -f -c ${cfg} --verbose --profile=p1 --key f_abc

# check files haven't been updated
lsd --tree ${basedir}
[ -e ${basedir}/dotfiles/a/newdir/b/c ] && echo "should not have been updated" && exit 1
[ ! -e ${basedir}/dotfiles/a/newdir/b/d ] && echo "should have been updated" && exit 1

## CLEANING
rm -rf ${basedir} ${tmpd}

echo "OK"
exit 0
