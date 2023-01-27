#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2021, deadc0de6
#
# test clear_workdir
# returns 1 in case of error
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
  bin="coverage run -a --source=dotdrop -m dotdrop.dotdrop"
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
[ "$?" != "0" ] && exit 1

[ ! -e "${tmpd}"/x ] && echo "f_x not installed" && exit 1
[ ! -h "${tmpd}"/x ] && echo "f_x not symlink" && exit 1
[ ! -e "${DOTDROP_WORKDIR}"/"${tmpd}"/x ] && echo "f_x not in workdir (${DOTDROP_WORKDIR}/${tmpd})" && exit 1

# add file
touch "${DOTDROP_WORKDIR}"/new

echo "[+] re-install with clear-workdir in cli"
cd "${ddpath}" | printf "y\n" | ${bin} install -W -c "${cfg}" -p p1 --verbose
[ "$?" != "0" ] && exit 1

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
cd "${ddpath}" | printf "y\n" | ${bin} install -W -c "${cfg}" -p p1 --verbose
[ "$?" != "0" ] && exit 1

[ ! -e "${tmpd}"/x ] && echo "f_x not installed" && exit 1
[ ! -h "${tmpd}"/x ] && echo "f_x not symlink" && exit 1
[ ! -e "${DOTDROP_WORKDIR}"/"${tmpd}"/x ] && echo "f_x not in workdir (${DOTDROP_WORKDIR}/${tmpd})" && exit 1
[ -e "${DOTDROP_WORKDIR}"/new ] && echo "workdir not cleared (2)" && exit 1

echo "OK"
exit 0
