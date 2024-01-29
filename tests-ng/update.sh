#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test updates
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
basedir=$(mktemp -d --suffix='-dotdrop-dotpath' || mktemp -d)
dotpath="${basedir}/dotfiles"
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${dotpath}"

# the dotfile to be imported
tmpd=$(mktemp -d --suffix='-dotdrop-fs' || mktemp -d)

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

# single file
echo 'unique' > "${tmpd}"/uniquefile

# hierarchy from https://pymotw.com/2/filecmp/
# create the hierarchy
# for dir1 (originally imported directory))))
mkdir "${tmpd}"/dir1
touch "${tmpd}"/dir1/file_only_in_dir1
mkdir -p "${tmpd}"/dir1/dir_only_in_dir1
touch "${tmpd}/dir1/dir_only_in_dir1/x"
mkdir -p "${tmpd}"/dir1/common_dir
touch "${tmpd}/dir1/common_dir/y"
echo 'this file is the same' > "${tmpd}"/dir1/common_file
echo 'in dir1' > "${tmpd}"/dir1/not_the_same
echo 'This is a file in dir1' > "${tmpd}"/dir1/file_in_dir1
mkdir -p "${tmpd}"/dir1/sub/sub2
mkdir -p "${tmpd}"/dir1/notindir2/notindir2
echo 'first' > "${tmpd}"/dir1/sub/sub2/different
#tree ${tmpd}/dir1

# create the hierarchy
# for dir2 (modified original for update)
mkdir "${tmpd}"/dir2
touch "${tmpd}"/dir2/file_only_in_dir2
mkdir -p "${tmpd}"/dir2/common_dir
touch "${tmpd}/dir2/common_dir/z"
echo 'this file is the same' > "${tmpd}"/dir2/common_file
echo 'in dir2' > "${tmpd}"/dir2/not_the_same
mkdir -p "${tmpd}"/dir2/file_in_dir1
mkdir -p "${tmpd}"/dir2/sub/sub2
echo 'modified' > "${tmpd}"/dir2/sub/sub2/different
mkdir -p "${tmpd}"/dir2/new/new2
touch "${tmpd}/dir2/new/new2/new"
mkdir -p "${tmpd}"/dir2/sub1/sub2/sub3/
touch "${tmpd}"/dir2/sub1/sub2/sub3/file
#tree ${tmpd}/dir2

# create the config file
cfg="${basedir}/config.yaml"
create_conf "${cfg}" # sets token

# import dir1
echo "[+] import"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/dir1
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/uniquefile

# let's see the dotpath
#tree ${basedir}/dotfiles

# change dir1 to dir2 in deployed
echo "[+] change dir"
rm -rf "${tmpd}"/dir1
mv "${tmpd}"/dir2 "${tmpd}"/dir1
#tree ${tmpd}/dir1

# change unique file
echo 'changed' > "${tmpd}"/uniquefile

# compare
#echo "[+] comparing"
#cd ${ddpath} | ${bin} compare -c ${cfg}

# update
echo "[+] updating"
cd "${ddpath}" | ${bin} update -c "${cfg}" -f --verbose "${tmpd}"/uniquefile "${tmpd}"/dir1
grep 'changed' "${dotpath}/${tmpd}/uniquefile"
[ ! -e "${dotpath}/${tmpd}/dir1/file_only_in_dir2" ] && echo "file_only_in_dir2 not found" && exit 1
[ -f "${dotpath}/${tmpd}/dir1/file_in_dir1" ] && echo "directory \"file_in_dir1\" not removed" && exit 1

# manually update
mkdir -p "${dotpath}/${tmpd}/dir1/file_in_dir1"

# ensure changes applied correctly
echo "diff dir1"
tree "${tmpd}"/dir1
diff -r --suppress-common-lines "${tmpd}"/dir1 "${dotpath}/${tmpd}/dir1"
echo "diff uniquefile"
diff "${tmpd}"/uniquefile "${basedir}"/dotfiles/"${tmpd}"/uniquefile
[ ! -e "${basedir}"/dotfiles/"${tmpd}"/dir1/sub1/sub2/sub3/file ] && echo "sub does not exist" && exit 1

echo "OK"
exit 0
