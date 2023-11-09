#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test importing link_children
# returns 1 in case of error
#

## start-cookie
set -eu -o errtrace -o pipefail
cur=$(cd "$(dirname "${0}")" && pwd)
ddpath="${cur}/../"
PPATH="{PYTHONPATH:-}"
export PYTHONPATH="${ddpath}:${PPATH}"
altbin="python3 -m dotdrop.dotdrop"
if hash coverage 2>/dev/null; then
  mkdir -p coverages/
  altbin="coverage run -p --data-file coverages/coverage --source=dotdrop -m dotdrop.dotdrop"
fi
bin="${DT_BIN:-${altbin}}"
# shellcheck source=tests-ng/helpers
source "${cur}"/helpers
echo -e "$(tput setaf 6)==> RUNNING $(basename "${BASH_SOURCE[0]}") <==$(tput sgr0)"
## end-cookie

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

# dotpath
dotpath="${tmps}/dotfiles"
mkdir -p "${dotpath}"

# create the dotfile to import
dt="${tmpd}/directory"
mkdir -p "${dt}"
# subdir
dtsub1="${dt}/sub1"
mkdir -p "${dtsub1}"
dtsub2="${dt}/sub2"
mkdir -p "${dtsub2}"
dtsub3="${dtsub1}/subsub1"
mkdir -p "${dtsub3}"
# files
f1="${dt}/file"
subf1="${dtsub1}/file"
subf2="${dtsub2}/file"
subf3="${dtsub3}/file"
touch "${f1}" "${subf1}" "${subf2}" "${subf3}"

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

# import
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V --link=link_children "${dt}"

# check is set to link_children
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -V -G | grep "d_$(basename "${dt}")" | grep ',link:link_children,'

# checks file exists in dotpath
[ ! -e "${dotpath}"/"${dt}" ] && echo "dotfile not imported" && exit 1
[ ! -e "${dotpath}"/"${dtsub1}" ] && echo "sub1 not found in dotpath" && exit 1
[ ! -e "${dotpath}"/"${dtsub2}" ] && echo "sub2 not found in dotpath" && exit 1
[ ! -e "${dotpath}"/"${dtsub3}" ] && echo "sub3 not found in dotpath" && exit 1
[ ! -e "${dotpath}"/"${f1}" ] && echo "f1 not found in dotpath" && exit 1
[ ! -e "${dotpath}"/"${subf1}" ] && echo "subf1 not found in dotpath" && exit 1
[ ! -e "${dotpath}"/"${subf2}" ] && echo "subf2 not found in dotpath" && exit 1
[ ! -e "${dotpath}"/"${subf3}" ] && echo "subf3 not found in dotpath" && exit 1

# checks file exists in fs
[ ! -e "${dt}" ] && echo "dotfile not imported" && exit 1
[ ! -e "${dtsub1}" ] && echo "sub1 not found in fs" && exit 1
[ ! -e "${dtsub2}" ] && echo "sub2 not found in fs" && exit 1
[ ! -e "${dtsub3}" ] && echo "sub3 not found in fs" && exit 1
[ ! -e "${f1}" ] && echo "f1 not found in fs" && exit 1
[ ! -e "${subf1}" ] && echo "subf1 not found in fs" && exit 1
[ ! -e "${subf2}" ] && echo "subf2 not found in fs" && exit 1
[ ! -e "${subf3}" ] && echo "subf3 not found in fs" && exit 1

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

# checks file have correct type in fs
[ ! -h "${f1}" ] && echo "f1 is not a symlink" && exit 1
[ -h "${subf1}" ] && echo "subf1 is not a regular file" && exit 1
[ -h "${subf2}" ] && echo "subf2 is not a regular file" && exit 1
[ -h "${subf3}" ] && echo "subf3 is not a regular file" && exit 1
[ ! -h "${dtsub1}" ] && echo "dtsub1 is not a symlink" && exit 1
[ ! -h "${dtsub2}" ] && echo "dtsub2 is not a symlink" && exit 1
[ -h "${dtsub3}" ] && echo "dtsub3 is not a regular directory" && exit 1

echo "OK"
exit 0
