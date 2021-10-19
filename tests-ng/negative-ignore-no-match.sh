#!/usr/bin/env bash
# author: jtt9340 (https://github.com/jtt9340)
#
# test that dotdrop warns when a negative ignore pattern
# does not match a file that would be ignored
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

# adding ignore in dotfile
cfg2="${basedir}/config2.yaml"
sed '/d_program:/a\
\ \ \ \ instignore:\
\ \ \ \ - "!*/ignore_me/c"
' ${cfg} > ${cfg2}

# install
rm -rf ${tmpd}
echo "[+] install with negative ignore in dotfile"
echo '(1) expect dotdrop install to warn when negative ignore pattern does not match an already-ignored file'

patt="[WARN] no files that are currently being ignored match \"*/ignore_me/c\". In order for a negative ignore
pattern to work, it must match a file that is being ignored by a previous ignore pattern."
cd ${ddpath} | ${bin} install -c ${cfg2} --verbose 2>&1 >/dev/null | grep -F "${patt}" ||
  (echo "dotdrop did not warn when negative ignore pattern did not match an already-ignored file" && exit 1)

echo "OK"
exit 0
