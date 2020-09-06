#!/usr/bin/env bash
# author: jtt9340 (https://github.com/jtt9340)
#
# test install negative ignore absolute/relative
# returns 1 in case of error
#

# exit on first error
#set -e

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

# dotdrop directory
basedir=`mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d`
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"

# the dotfile to be imported
tmpd=`mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d`

# some files
mkdir -p ${tmpd}/program/ignore_me
echo "some data" > ${tmpd}/program/a
echo "some data" > ${tmpd}/program/ignore_me/b
echo "some data" > ${tmpd}/program/ignore_me/c

# create the config file
cfg="${basedir}/config.yaml"
create_conf ${cfg} # sets token

# import
echo "[+] import"
cd ${ddpath} | ${bin} import -c ${cfg} ${tmpd}/program

# adding ignore in dotfile
cfg2="${basedir}/config2.yaml"
sed '/d_program:/a\
\ \ \ \ instignore:\
\ \ \ \ - "*/ignore_me/*"\
\ \ \ \ - "!*/ignore_me/c"
' ${cfg} > ${cfg2}

# install
rm -rf ${tmpd}
echo "[+] install with negative ignore in dotfile"
cd ${ddpath} | ${bin} install -c ${cfg2} --verbose
[ "$?" != "0" ] && exit 1
echo '(1) expect structure to be
.
└── program
 ├── a
 └── ignore_me
    └── c'

[[ -n "$(find ${tmpd}/program -name a)" ]] || exit 1
echo "(1) found program/a ... good"
[[ -n "$(find ${tmpd}/program/ignore_me -name b)" ]] && exit 1
echo "(1) didn't find program/b ... good"
[[ -n "$(find ${tmpd}/program/ignore_me -name c)" ]] || exit 1
echo "(1) found program/c ... good"

## CLEANING
rm -rf ${basedir} ${tmpd}

echo "OK"
exit 0

