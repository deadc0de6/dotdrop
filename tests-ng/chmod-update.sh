#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2020, deadc0de6
#
# test chmod on update
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
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the dotfile
dnormal="${tmpd}/dir_normal"
mkdir -p "${dnormal}"
echo "dir_normal/f1" > "${dnormal}"/file1
echo "dir_normal/f2" > "${dnormal}"/file2

dlink="${tmpd}/dir_link"
mkdir -p "${dlink}"
echo "dir_link/f1" > "${dlink}"/file1
echo "dir_link/f2" > "${dlink}"/file2

dlinkchildren="${tmpd}/dir_link_children"
mkdir -p "${dlinkchildren}"
echo "dir_linkchildren/f1" > "${dlinkchildren}"/file1
echo "dir_linkchildren/f2" > "${dlinkchildren}"/file2

fnormal="${tmpd}/filenormal"
echo "filenormal" > "${fnormal}"

flink="${tmpd}/filelink"
echo "filelink" > "${flink}"

toimport="${dnormal} ${dlink} ${dlinkchildren} ${fnormal} ${flink}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF

# import
for i in ${toimport}; do
  cd "${ddpath}" | ${bin} import -c "${cfg}" -f -p p1 -V "${i}"
done

cat "${cfg}"

# test no chmod
cnt=$(cat "${cfg}" | ( grep chmod || : ) | wc -l)
[ "${cnt}" != "0" ] && echo "chmod wrongly inserted" && exit 1

######################
# update dnormal
chmod 777 "${dnormal}"
cd "${ddpath}" | ${bin} update -c "${cfg}" -f -p p1 -V "${dnormal}"

# check rights updated
bname=$(basename "${dnormal}")
[ "$(stat -c '%a' "${tmps}"/dotfiles/"${tmpd}"/"${bname}")" != "777" ] && echo "rights not updated (1)" && exit 1

cnt=$(cat "${cfg}" | grep "chmod: '777'" | wc -l)
[ "${cnt}" != "1" ] && echo "chmod not updated (1)" && exit 1

######################
# update dlink
chmod 777 "${dlink}"
cd "${ddpath}" | ${bin} update -c "${cfg}" -f -p p1 -V "${dlink}"

# check rights updated
bname=$(basename "${dlink}")
[ "$(stat -c '%a' "${tmps}"/dotfiles/"${tmpd}"/"${bname}")" != "777" ] && echo "rights not updated (2)" && exit 1
cnt=$(cat "${cfg}" | grep "chmod: '777'" | wc -l)
[ "${cnt}" != "2" ] && echo "chmod not updated (2)" && exit 1

######################
# update dlinkchildren
chmod 777 "${dlinkchildren}"
cd "${ddpath}" | ${bin} update -c "${cfg}" -f -p p1 -V "${dlinkchildren}"

# check rights updated
bname=$(basename "${dlinkchildren}")
[ "$(stat -c '%a' "${tmps}"/dotfiles/"${tmpd}"/"${bname}")" != "777" ] && echo "rights not updated (3)" && exit 1
cnt=$(cat "${cfg}" | grep "chmod: '777'" | wc -l)
[ "${cnt}" != "3" ] && echo "chmod not updated (3)" && exit 1

######################
# update fnormal
chmod 777 "${fnormal}"
cd "${ddpath}" | ${bin} update -c "${cfg}" -f -p p1 -V "${fnormal}"

# check rights updated
bname=$(basename "${fnormal}")
[ "$(stat -c '%a' "${tmps}"/dotfiles/"${tmpd}"/"${bname}")" != "777" ] && echo "rights not updated (4)" && exit 1
cnt=$(cat "${cfg}" | grep "chmod: '777'" | wc -l)
[ "${cnt}" != "4" ] && echo "chmod not updated (4)" && exit 1

######################
# update flink
chmod 777 "${flink}"
cd "${ddpath}" | ${bin} update -c "${cfg}" -f -p p1 -V "${flink}"

# check rights updated
bname=$(basename "${flink}")
[ "$(stat -c '%a' "${tmps}"/dotfiles/"${tmpd}"/"${bname}")" != "777" ] && echo "rights not updated (5)" && exit 1
cnt=$(cat "${cfg}" | grep "chmod: '777'" | wc -l)
[ "${cnt}" != "5" ] && echo "chmod not updated (5)" && exit 1

echo "OK"
exit 0
