#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test action template execution
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

# Convenience function to grep into a file and exit with an erro message if the
# content is not found
should_grep() {
    SHOULD_GREP_STR="$1"
    SHOULD_GREP_FILE="$2"

    grep "$SHOULD_GREP_STR" "$SHOULD_GREP_FILE" > /dev/null || {
        echo >&2 "$SHOULD_GREP_STR not found in $SHOULD_GREP_FILE"
        exit 1
    }

    unset SHOULD_GREP_FILE SHOULD_GREP_STR
}

# the action temp
tmpa=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
# the dotfile source
tmps=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`
mkdir -p ${tmps}/dotfiles
# the dotfile destination
tmpd=`mktemp -d --suffix='-dotdrop-tests' || mktemp -d`

# create the config file
cfg="${tmps}/config.yaml"

cat > ${cfg} << _EOF
actions:
  pre:
    preaction: "echo {0} > {1}"
  post:
    postaction: "echo {0} > ${tmpa}/post"
  nakedaction: "echo {0} > ${tmpa}/naked"
  profileaction: "echo {0} >> ${tmpa}/profile"
  dynaction: "echo {0} > ${tmpa}/dyn"
config:
  backup: true
  create: true
  dotpath: dotfiles
  default_actions:
  - preaction '{{@@ var_pre @@}}' "${tmpa}/pre"
  - postaction '{{@@ var_post @@}}'
  - nakedaction '{{@@ var_naked @@}}'
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
    actions:
    - profileaction '{{@@ var_profile @@}}'
    - dynaction '{{@@ user_name @@}}'
    include:
    - p2
  p2:
    dotfiles:
    - f_abc
    actions:
    - profileaction '{{@@ var_profile_2 @@}}'
    variables:
      var_profile_2: profile_var_2
variables:
  var_pre: pre_var
  var_post: post_var
  var_naked: naked_var
  var_profile: profile_var
dynvariables:
  user_name: 'echo $USER'
_EOF
#cat ${cfg}

# create the dotfile
echo 'test' > ${tmps}/dotfiles/abc

# install
cd ${ddpath} | ${bin} install -f -c ${cfg} -p p1 -V

# checks action
[ ! -e ${tmpa}/pre ] && echo 'pre action not executed' && exit 1
[ ! -e ${tmpa}/post ] && echo 'post action not executed' && exit 1
[ ! -e ${tmpa}/naked ] && echo 'naked action not executed'  && exit 1
[ ! -e ${tmpa}/profile ] && echo 'profile action not executed'  && exit 1
[ ! -e ${tmpa}/dyn ] && echo 'dynamic acton action not executed'  && exit 1
should_grep pre_var ${tmpa}/pre
should_grep post_var ${tmpa}/post
should_grep naked_var ${tmpa}/naked
should_grep profile_var ${tmpa}/profile
should_grep profile_var_2 ${tmpa}/profile
should_grep "$USER" ${tmpa}/dyn

## CLEANING
rm -rf ${tmps} ${tmpd} ${tmpa}

echo "OK"
exit 0
