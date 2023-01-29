#!/usr/bin/env bash
# author: davla (https://github.com/davla)
# Copyright (c) 2022, deadc0de6
#
# test error report on importing the same sub-config file more than once
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

# dotfile source path
src="$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)"
mkdir -p "${src}/dotfiles"
clear_on_exit "${src}"

# dotfile destination
dst="$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)"
clear_on_exit "${dst}"
error_log="${dst}/error.log"

# bottom-level
bottom_level_cfg="${src}/bottom-level.yaml"
cat > "${bottom_level_cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: ${src}/dotfiles

dotfiles: []
profiles: []
_EOF
touch "${src}/dotfiles/bottom"

# mid-level
mid_level_cfg="${src}/mid-level.yaml"
cat > "${mid_level_cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: ${src}/dotfiles
  import_configs:
  - ${bottom_level_cfg}

dotfiles: []

profiles: []
_EOF

# top-level
top_level_cfg="${src}/top-level.yaml"
cat > "${top_level_cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: ${src}/dotfiles
  import_configs:
  - ${mid_level_cfg}
  - ${bottom_level_cfg}

dotfiles: []

profiles: []
_EOF

# install
set +e
cd "${ddpath}" | ${bin} install -f -c "${top_level_cfg}" -p top-level 2> "${error_log}"
set -e

# checks
grep "${bottom_level_cfg} imported more than once in ${top_level_cfg}" "${error_log}" > /dev/null 2>&1

echo "OK"
exit 0
