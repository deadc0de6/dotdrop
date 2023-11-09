#!/usr/bin/env bash
# author: davla (https://github.com/davla)
# Copyright (c) 2022, deadc0de6
#
# test error report on importing the same sub-config file more than once
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
