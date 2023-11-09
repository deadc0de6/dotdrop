#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test duplicate keys
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

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the imported one
mkdir -p "${tmps}"/dotfiles/"${tmpd}"
echo "test" > "${tmps}"/dotfiles/"${tmpd}"/abc
echo "test" > "${tmpd}"/abc

# create the to-be-imported
mkdir -p "${tmpd}"/sub
echo "test2" > "${tmpd}"/sub/abc

mkdir -p "${tmpd}"/sub/sub2
echo "test2" > "${tmpd}"/sub/sub2/abc

mkdir -p "${tmpd}"/sub/sub
echo "test2" > "${tmpd}"/sub/sub/abc

# import
cd "${ddpath}" | ${bin} import -f --verbose -c "${cfg}" -p p2 \
  "${tmpd}"/abc \
  "${tmpd}"/sub/abc \
  "${tmpd}"/sub/abc \
  "${tmpd}"/sub/sub/abc \
  "${tmpd}"/sub/sub2/abc

# count dotfiles for p2
cnt=$(cd "${ddpath}" | ${bin} files --verbose -c "${cfg}" -p p2 -b | grep '^f_' | wc -l)
[ "${cnt}" != "4" ] && echo "bad count for p2: ${cnt} != 4" && exit 1

echo "OK"
exit 0
