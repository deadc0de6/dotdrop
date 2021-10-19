#!/usr/bin/env bash
# author: jtt9340 (https://github.com/jtt9340)
#
# test compare negative ignore relative
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

# dotdrop directory
basedir=`mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d`
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"

# the dotfile to be imported
tmpd=`mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d`

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

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
cd ${ddpath} | ${bin} import -f -c ${cfg} ${tmpd}/program

# make some changes to generate a diff
echo "some other data" > ${tmpd}/program/a
echo "some other data" > ${tmpd}/program/ignore_me/b
echo "some other data" > ${tmpd}/program/ignore_me/c

# expects two diffs (no need to test comparing normal - 3 diffs, as that is taken care of in compare-negative-ignore.sh)
patt0="ignore_me/*"
patt1="!ignore_me/c"
echo "[+] comparing with ignore (patterns: ${patt0} and ${patt1}) - 2 diffs"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose --ignore=${patt0} --ignore=${patt1}
[ "$?" = "0" ] && exit 1
set -e

########################################
# Test ignores specified in config.yaml
########################################
# add some files
mkdir -p ${tmpd}/.zsh
echo "some data" > ${tmpd}/.zsh/somefile
mkdir -p ${tmpd}/.zsh/plugins
echo "some data" > ${tmpd}/.zsh/plugins/someplugin

echo "[+] import .zsh"
cd ${ddpath} | ${bin} import -f -c ${cfg} ${tmpd}/.zsh

touch ${tmpd}/.zsh/plugins/ignore-1.zsh
touch ${tmpd}/.zsh/plugins/ignore-2.zsh

# adding ignore in config.yaml
cfg2="${basedir}/config2.yaml"
sed '/d_zsh:/a\
\ \ \ \ cmpignore:\
\ \ \ \ - "plugins/ignore-?.zsh"\
\ \ \ \ - "!plugins/ignore-2.zsh"
' ${cfg} > ${cfg2}

# expects one diff
patt0="plugins/ignore-?.zsh"
patt1="!plugins/ignore-2.zsh"
echo "[+] comparing with ignore (patterns: ${patt0} and ${patt1}) - 1 diff"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg} --verbose -C ${tmpd}/.zsh --ignore=${patt0} --ignore=${patt1}
[ "$?" = "0" ] && exit 1
set -e

# expects one diff
echo "[+] comparing .zsh with ignore in dotfile - 1 diff expected"
set +e
cd ${ddpath} | ${bin} compare -c ${cfg2} --verbose -C ${tmpd}/.zsh
ret="$?"
echo ${ret}
[ "${ret}" = "0" ] && exit 1
set -e

echo "OK"
