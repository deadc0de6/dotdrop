#!/usr/bin/env bash
# author: jtt9340 (https://github.com/jtt9340)
#
# test templating a symlink
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
# expected
expected=$(mktemp --suffix='-dotdrop-tests' || mktemp)
echo "expected: ${expected}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpw}"
clear_on_exit "${expected}"

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
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the expected output
cat > "${expected}" << _EOF
p1
blabla
_EOF

# create the dotfile
echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/ghi
echo "blabla" >> "${tmps}"/dotfiles/ghi
# dotfile is actually a symlink to a different file
ln -s "${tmps}"/dotfiles/ghi "${tmps}"/dotfiles/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b -V

# checks
[ ! -e "${tmpd}"/abc ] && echo "[ERROR] dotfile not installed" && exit 1
diff "${tmpd}"/abc "${expected}" || {
  echo "[ERROR] dotfile not processed by template engine"
  exit 1
}

# test multiple levels of indirection
ln -s "${tmps}"/dotfiles/ghi "${tmps}"/dotfiles/def
ln -s -f "${tmps}"/dotfiles/def "${tmps}"/dotfiles/abc

# install again
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b -V

# checks again
[ ! -e "${tmpd}"/abc ] && echo "[ERROR] dotfile not installed" && exit 1
diff "${tmpd}"/abc "${expected}" || {
  echo "[ERROR] dotfile not processed by template engine"
  exit 1
}

echo "OK"
exit 0
