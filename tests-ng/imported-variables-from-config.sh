#!/usr/bin/env bash
# author: davla (https://github.com/davls)
# Copyright (c) 2020, davla
#
# test variables imported from config and used in the importing yaml config
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
subcfg="${tmps}/subconfig.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_configs:
  - ${subcfg}
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: '{{@@ abc_dyn_src @@}}{{@@ abc_src @@}}'
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
cat "${cfg}"

# create the subconfig file
cat > "${subcfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
variables:
  abc_src: c
dynvariables:
  abc_dyn_src: 'echo ab'
dotfiles: []
profiles: []
_EOF

# create the dotfile
dirname "${tmps}"/dotfiles/abc | xargs mkdir -p
cat > "${tmps}"/dotfiles/abc << _EOF
Hell yeah
_EOF

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

# test file existence and content
[ -f "${tmpd}/abc" ] || {
    echo 'Dotfile not installed'
    exit 1
}

echo "OK"
exit 0
