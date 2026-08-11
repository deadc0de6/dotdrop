#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2026, deadc0de6
#
# test removing stale links installed with link_children
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
source_dir="${basedir}/dotfiles/skills"

# deployed directory
destination=$(mktemp -d --suffix='-dotdrop-fs' || mktemp -d)

clear_on_exit "${basedir}"
clear_on_exit "${destination}"

# create the config file
cfg="${basedir}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  d_skills:
    src: skills
    dst: ${destination}
    link: link_children
    template: false
profiles:
  p1:
    dotfiles:
    - d_skills
_EOF

# create managed and unmanaged destination entries
mkdir -p "${source_dir}/kept-skill"
mkdir -p "${source_dir}/removed-skill"
mkdir -p "${destination}/.system"
echo 'local' > "${destination}/local-file"
ln -s "${basedir}/unrelated-missing" "${destination}/unrelated-link"

# install the managed links
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1
[ ! -h "${destination}/kept-skill" ] && echo "kept-skill not linked" && exit 1
[ ! -h "${destination}/removed-skill" ] && echo "removed-skill not linked" && exit 1

# remove one source child and ensure pruning remains opt-in
rm -rf "${source_dir}/removed-skill"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1
[ ! -h "${destination}/removed-skill" ] && echo "stale link removed without opt-in" && exit 1

# dry run must report the stale link without removing it
out=$(cd "${ddpath}" | ${bin} install --remove-existing --dry -f -c "${cfg}" -p p1)
echo "${out}"
echo "${out}" | grep -F "would remove stale link \"${destination}/removed-skill\"" >/dev/null
[ ! -h "${destination}/removed-skill" ] && echo "stale link removed during dry run" && exit 1

# remove only the stale managed link
cd "${ddpath}" | ${bin} install --remove-existing -f -c "${cfg}" -p p1
[ -h "${destination}/removed-skill" ] && echo "stale link not removed" && exit 1
[ ! -h "${destination}/kept-skill" ] && echo "live link removed" && exit 1
[ ! -h "${destination}/unrelated-link" ] && echo "unrelated link removed" && exit 1
[ ! -d "${destination}/.system" ] && echo "local directory removed" && exit 1
[ ! -f "${destination}/local-file" ] && echo "local file removed" && exit 1

echo "OK"
exit 0
