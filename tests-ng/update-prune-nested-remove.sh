#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2026, deadc0de6
#
# ensure update prunes nested removals
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

# dotdrop directory
basedir=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
dotpath="${basedir}/dotfiles"

# deployed directory
deployed=$(mktemp -d --suffix='-dotdrop-fs' || mktemp -d)
rel_deployed="${deployed#/}"

# misc files to cleanup
outlog=$(mktemp -t dotdrop-update-XXXX || mktemp)

clear_on_exit "${basedir}"
clear_on_exit "${deployed}"
clear_on_exit "${outlog}"

# create the config file
cfg="${basedir}/config.yaml"
create_conf "${cfg}"

# create deployed content
mkdir -p "${deployed}/sub"
echo 'config' > "${deployed}/config.yaml"
echo 'style' > "${deployed}/style.css"
echo 'test' > "${deployed}/sub/test"

# import the directory
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${deployed}"

# remove the nested directory on the filesystem
rm -rf "${deployed}/sub"

# update dotpath and capture output
cd "${ddpath}" | ${bin} update -f --verbose -c "${cfg}" "${deployed}" | tee "${outlog}"

# ensure sub removed from dotpath
[ -d "${dotpath}/${rel_deployed}/sub" ] && echo "sub directory not removed from dotpath" && exit 1
[ -e "${dotpath}/${rel_deployed}/sub/test" ] && echo "nested file still present in dotpath" && exit 1

# ensure only top-level removal is logged once
count_sub=$( (grep -F "\"${dotpath}/${rel_deployed}/sub\" removed" "${outlog}" || true) | wc -l | tr -d ' ')
count_sub_slash=$( (grep -F "\"${dotpath}/${rel_deployed}/sub/\" removed" "${outlog}" || true) | wc -l | tr -d ' ')
count_nested=$( (grep -F "\"${dotpath}/${rel_deployed}/sub/test\" removed" "${outlog}" || true) | wc -l | tr -d ' ')
count_nested_slash=$( (grep -F "\"${dotpath}/${rel_deployed}/sub/test/\" removed" "${outlog}" || true) | wc -l | tr -d ' ')

total_sub=$((count_sub + count_sub_slash))
[ "${total_sub}" -ne 1 ] && echo "expected single removal of sub directory, got ${total_sub}" && exit 1

total_nested=$((count_nested + count_nested_slash))
[ "${total_nested}" -ne 0 ] && echo "unexpected nested removal logged" && exit 1

echo "OK"
exit 0
