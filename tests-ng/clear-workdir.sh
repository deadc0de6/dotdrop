#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2021, deadc0de6
#
# test clear_workdir
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
mkdir -p "${basedir}"/dotfiles
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
if [ -z "${DOTDROP_WORKDIR}" ]; then
  tmpw=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
  export DOTDROP_WORKDIR="${tmpw}"
  clear_on_exit "${tmpw}"
fi

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

echo "{{@@ profile @@}}" > "${basedir}"/dotfiles/x

# create the config file
cfg="${basedir}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_x:
    src: x
    dst: ${tmpd}/x
    link: link
profiles:
  p1:
    dotfiles:
    - f_x
_EOF

echo "[+] install (1)"
cd "${ddpath}" | ${bin} install -c "${cfg}" -f -p p1 --verbose | grep '^1 dotfile(s) installed.$'
ret="$?"
[ "${ret}" != "0" ] && echo "install returned ${ret}" && exit 1

# checks
[ ! -e "${tmpd}"/x ] && echo "f_x not installed (${tmpd}/x)" && exit 1
[ ! -h "${tmpd}"/x ] && echo "f_x not symlink (${tmpd}/x)" && exit 1
[ ! -e "${DOTDROP_WORKDIR}"/"${tmpd}"/x ] && echo "f_x not in workdir (${DOTDROP_WORKDIR}/${tmpd})" && exit 1

# add file
touch "${DOTDROP_WORKDIR}"/new

echo "[+] re-install with clear-workdir in cli"
(
  cd "${ddpath}"
  printf "y\n" | ${bin} install -W -c "${cfg}" -p p1 --verbose
  exit $?
)

[ ! -e "${tmpd}"/x ] && echo "f_x not installed" && exit 1
[ ! -h "${tmpd}"/x ] && echo "f_x not symlink" && exit 1
[ ! -e "${DOTDROP_WORKDIR}"/"${tmpd}"/x ] && echo "f_x not in workdir (${DOTDROP_WORKDIR}/${tmpd})" && exit 1
[ -e "${DOTDROP_WORKDIR}"/new ] && echo "workdir not cleared (1)" && exit 1

# add file
touch "${DOTDROP_WORKDIR}"/new

echo "[+] re-install with config clear-workdir in config"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  clear_workdir: true
dotfiles:
  f_x:
    src: x
    dst: ${tmpd}/x
    link: link
profiles:
  p1:
    dotfiles:
    - f_x
_EOF
(
  cd "${ddpath}"
  printf "y\n" | ${bin} install -W -c "${cfg}" -p p1 --verbose
  exit $?
)

[ ! -e "${tmpd}"/x ] && echo "f_x not installed" && exit 1
[ ! -h "${tmpd}"/x ] && echo "f_x not symlink" && exit 1
[ ! -e "${DOTDROP_WORKDIR}"/"${tmpd}"/x ] && echo "f_x not in workdir (${DOTDROP_WORKDIR}/${tmpd})" && exit 1
[ -e "${DOTDROP_WORKDIR}"/new ] && echo "workdir not cleared (2)" && exit 1

echo "OK"
exit 0
