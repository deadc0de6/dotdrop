#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test updates and rights
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
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"

# the dotfile directory to be imported
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
# the dotfile file to be imported
tmpf=$(mktemp)

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

# single file
echo 'file' > "${tmpf}"

mkdir "${tmpd}"/dir1
echo 'dir1file1' > "${tmpd}"/dir1/file1
echo 'dir1file2' > "${tmpd}"/dir1/file2

# create the config file
cfg="${basedir}/config.yaml"
create_conf "${cfg}" # sets token

# import dir1
echo "[+] import"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpf}"

# change file
chmod +x "${tmpf}"

# update
echo "[+] updating"
cd "${ddpath}" | ${bin} update -c "${cfg}" -f --verbose "${tmpf}"

# test change applied
[ "$(stat -c '%a' "${tmpf}")" != "$(stat -c '%a' "${basedir}"/dotfiles/"${tmpf}")" ] && exit 1

# change file
chmod +x "${tmpd}"/dir1/file2
echo 'test' > "${tmpd}"/dir1/newfile
chmod +x "${tmpd}"/dir1/newfile

# update
echo "[+] updating"
cd "${ddpath}" | ${bin} update -c "${cfg}" -f --verbose "${tmpd}"

# test change applied
[ "$(stat -c '%a' "${tmpd}"/dir1/newfile)" != "$(stat -c '%a' "${basedir}"/dotfiles/"${tmpd}"/dir1/newfile)" ] && exit 1
[ "$(stat -c '%a' "${tmpd}"/dir1/file2)" != "$(stat -c '%a' "${basedir}"/dotfiles/"${tmpd}"/dir1/file2)" ] && exit 1

echo "OK"
exit 0
