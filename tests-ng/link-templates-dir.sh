#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test link of directory containing templates
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
echo "dotfiles source (dotpath): ${tmps}"
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
echo "dotfiles destination: ${tmpd}"
# the workdir
tmpw=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
export DOTDROP_WORKDIR="${tmpw}"
echo "workdir: ${tmpw}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpw}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  workdir: ${tmpw}
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    link: true
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
mkdir -p "${tmps}"/dotfiles/abc
echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/abc/template
echo "blabla" >> "${tmps}"/dotfiles/abc/template
echo "blabla" > "${tmps}"/dotfiles/abc/nottemplate

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b -V

# checks
[ ! -d "${tmpd}"/abc ] && echo "[ERROR] dotfile not installed" && exit 1
[ ! -h "${tmpd}"/abc ] && echo "[ERROR] dotfile is not a symlink" && exit 1
#cat ${tmpd}/abc/template
#tree -a ${tmpd}/abc/
set +e
grep '{{@@' "${tmpd}"/abc/template >/dev/null 2>&1 && echo "[ERROR] template in dir not replace" && exit 1
set -e

echo "OK"
exit 0
