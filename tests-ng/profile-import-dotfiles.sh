#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6
#
# test dotfiles imported in profile
# and importing
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
[ ! -d "${ddpath}" ] && echo "ddpath \"${ddpath}\" is not a directory" && exit 1

export PYTHONPATH="${ddpath}:${PYTHONPATH}"
bin="python3 -m dotdrop.dotdrop"
if hash coverage 2>/dev/null; then
  bin="coverage run -p --source=dotdrop -m dotdrop.dotdrop"
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

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"
cfg2="${tmps}/dotfiles.yaml"

src="dotdrop-test"
dst=".dotdrop-test"
clear_on_exit "${HOME}/${dst}"

cat > "${cfg}" << _EOF
config:
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
  f_def:
    dst: ~/${dst}
    src: ${src}
profiles:
  p1:
    import:
    - dotfiles.yaml
    dotfiles:
    - f_abc
_EOF
cat "${cfg}"

cat > "${cfg2}" << _EOF
dotfiles:
  - f_def
_EOF
#cat ${cfg2}

# create the dotfile
echo "abc" > "${tmps}"/dotfiles/abc
echo "abc" > "${tmpd}"/abc
echo "def" > "${tmps}"/dotfiles/${src}
echo "def" > "${HOME}"/${dst}

# import
## this is a special case since the dotfile must
## be in home (because it is strip)
echo "${ddpath}"
echo "${bin}"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 --verbose ~/${dst}

cat "${cfg}"
echo '----------'
cat "${cfg2}"

cnt=$(cd "${ddpath}" | ${bin} files -G -c "${cfg}" -p p1 | grep '^f_def' | wc -l)
[ "${cnt}" != "1" ] && echo "imported twice! (${cnt})" && exit 1

echo "OK"
exit 0
