#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6
#
# test import to no profile (using ALL keyword)
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
[ ! -d "${ddpath}" ] && echo "ddpath \"${ddpath}\" is not a directory" && exit 1

export PYTHONPATH="${ddpath}:${PYTHONPATH}"
bin="python3 -m dotdrop.dotdrop"
if hash coverage 2>/dev/null; then
  bin="coverage run -a --source=dotdrop -m dotdrop.dotdrop"
fi

echo "dotdrop path: ${ddpath}"
echo "pythonpath: ${PYTHONPATH}"

# get the helpers
# shellcheck source=tests-ng/helpers
source "${cur}"/helpers

echo -e "$(tput setaf 6)==> RUNNING $(basename "${BASH_SOURCE[0]}") <==$(tput sgr0)"

################################################################
# this is the test
################################################################

# the dotfile source
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the dotfile
echo "file1" > "${tmpd}"/file1
echo "file2" > "${tmpd}"/file2

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF
#cat ${cfg}

noprofile="ALL"

##################################
# import with profile from arg
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p "${noprofile}" -V "${tmpd}"/file1
cat "${cfg}"

# ensure exists and is not link
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/file1 ] && echo "file not imported" && exit 1
# ensure present in config
cat "${cfg}" | grep "${tmpd}"/file1 >/dev/null 2>&1

nb=$(cat "${cfg}" | grep f_file1 | wc -l)
[ "${nb}" != "1" ] && echo 'bad config' && exit 1

cntpre=$(find "${tmps}"/dotfiles -type f | wc -l)

# reimport
set +e
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p "${noprofile}" -V "${tmpd}"/file1
set -e
cat "${cfg}"

cntpost=$(find "${tmps}"/dotfiles -type f | wc -l)
[ "${cntpost}" != "${cntpre}" ] && echo "imported twice" && exit 1

nb=$(cat "${cfg}" | grep "dst: ${tmpd}/file1" | wc -l)
[ "${nb}" != "1" ] && echo 'imported twice in config' && exit 1

##################################
# import with profile from env
export DOTDROP_PROFILE="${noprofile}"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -V "${tmpd}"/file2
cat "${cfg}"

# ensure exists and is not link
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/file2 ] && echo "file not imported" && exit 1
# ensure present in config
cat "${cfg}" | grep "${tmpd}"/file2 >/dev/null 2>&1

nb=$(cat "${cfg}" | grep f_file2 | wc -l)
[ "${nb}" != "1" ] && echo 'bad config' && exit 1

cntpre=$(find "${tmps}"/dotfiles -type f | wc -l)

# reimport
set +e
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -V "${tmpd}"/file2
set -e
cat "${cfg}"

cntpost=$(find "${tmps}"/dotfiles -type f | wc -l)
[ "${cntpost}" != "${cntpre}" ] && echo "imported twice" && exit 1

nb=$(cat "${cfg}" | grep "dst: ${tmpd}/file2" | wc -l)
[ "${nb}" != "1" ] && echo 'imported twice in config' && exit 1

echo "OK"
exit 0
