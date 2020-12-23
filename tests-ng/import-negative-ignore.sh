#!/usr/bin/env bash
# author: jtt9340 (https://github.com/jtt9340)
#
# test negative ignore import
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

# dotdrop path can be pass as argument
ddpath="${cur}/../"
[ -n "${1}" ] && ddpath="${1}"
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
basedir=`mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d`
mkdir -p ${basedir}/dotfiles

# the dotfile destination
tmpd=`mkdir -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d`

# dotdrop directory
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"
mkdir -p ${tmpd}/a/{b,c}
echo 'a' > ${tmpd}/a/b/abfile1
echo 'a' > ${tmpd}/a/b/abfile2
echo 'a' > ${tmpd}/a/b/abfile3
echo 'a' > ${tmpd}/a/c/acfile
mkdir -p ${tmpd}/a/newdir/b
touch ${tmpd}/a/newdir/b/{c,d}

# create the config file
cfg="${basedir}/config.yaml"
cfg2="${basedir}/config2.yaml"
create_conf ${cfg} # sets token
sed '/dotpath: dotfiles/a\
\ \ impignore:\
\ \ \ \ - "*/newdir/b/*"\
\ \ \ \ - "!*/newdir/b/d"\
\ \ \ \ - "*/abfile?"\
\ \ \ \ - "!*/abfile3"
' ${cfg} > ${cfg2}

# import
echo "[+] import"
cd ${ddpath} | ${bin} import -f -c ${cfg2} --verbose --profile=p1 ${tmpd}/a --as=~/a

# check files haven't been imported
[ -e ${basedir}/dotfiles/a/newdir/b/c ] && echo "newdir/b/c should not have been imported" && exit 1
[ ! -e ${basedir}/dotfiles/a/newdir/b/d ] && echo "newdir/b/d should have been imported" && exit 1
[ -e ${basedir}/dotfiles/a/b/abfile1 ] && echo "abfile1 should not have been imported" && exit 1
[ -e ${basedir}/dotfiles/a/b/abfile2 ] && echo "abfile2 should not have been imported" && exit 1
[ ! -e ${basedir}/dotfiles/a/b/abfile3 ] && echo "abfile3 should have been imported" && exit 1

## CLEANING
rm -rf ${tmpd} ${basedir}

echo "OK"
exit 0
