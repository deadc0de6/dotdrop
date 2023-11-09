#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test transformations
# for install and compare
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

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"

# token
token="test-base64"
tokend="compressed archive"
touched="touched"

cat > "${cfg}" << _EOF
trans_read:
  base64: cat {0} | base64 -d > {1}
  uncompress: mkdir -p {1} && tar -xf {0} -C {1}
trans_write:
  base64: cat {0} | base64 > {1}
  compress: tar -cf {1} -C {0} .
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_def:
    dst: ${tmpd}/def
    src: def
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    trans_read: base64
    trans_write: base64
  d_ghi:
    dst: ${tmpd}/ghi
    src: ghi
    trans_read: uncompress
    trans_write: compress
    chmod: 700
profiles:
  p1:
    dotfiles:
    - f_abc
    - f_def
    - d_ghi
_EOF
#cat ${cfg}

# create the base64 dotfile
tmpf=$(mktemp --suffix='-dotdrop-tests' || mktemp -d)
echo ${token} > "${tmpf}"
cat "${tmpf}" | base64 > "${tmps}"/dotfiles/abc
rm -f "${tmpf}"

# create the canary dotfile
echo 'marker' > "${tmps}"/dotfiles/def

# create the compressed dotfile
tmpx=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
clear_on_exit "${tmpx}"
mkdir -p "${tmpx}"/{a,b,c}
mkdir -p "${tmpx}"/a/{dir1,dir2}
# ambiguous redirect ??
#echo ${tokend} > ${tmpd}/{a,b,c}/somefile
echo "${tokend}" > "${tmpx}"/a/somefile
echo "${tokend}" > "${tmpx}"/b/somefile
echo "${tokend}" > "${tmpx}"/c/somefile
echo "${tokend}" > "${tmpx}"/a/dir1/otherfile
# create a fake file to ensure dir is created
echo "${tokend}" > "${tmpx}"/a/dir2/token
tar -cf "${tmps}"/dotfiles/ghi -C "${tmpx}" .
rm -rf "${tmpx}"
tar -tf "${tmps}"/dotfiles/ghi

###########################
# test install and compare
###########################

echo "[+] run install"
# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b -V

# check canary dotfile
[ ! -e "${tmpd}"/def ] && echo "def does not exist" && exit 1

# check base64 dotfile
[ ! -e "${tmpd}"/abc ] && echo "abc does not exist" && exit 1
content=$(cat "${tmpd}"/abc)
[ "${content}" != "${token}" ] && echo "bad content for abc" && exit 1

# check directory dotfile
[ ! -e "${tmpd}"/ghi/a/dir1/otherfile ] && echo "otherfile does not exist" && exit 1
content=$(cat "${tmpd}"/ghi/a/somefile)
[ "${content}" != "${tokend}" ] && echo "bad content for somefile" && exit 1
content=$(cat "${tmpd}"/ghi/a/dir1/otherfile)
[ "${content}" != "${tokend}" ] && echo "bad content for otherfile" && exit 1

# compare
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1 -b -V
[ "$?" != "0" ] && echo "compare failed (0)" && exit 1
set -e

# change base64 deployed file
echo ${touched} > "${tmpd}"/abc
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1 -b -V
[ "$?" != "1" ] && echo "compare failed (1)" && exit 1
set -e

# change uncompressed deployed dotfile
echo ${touched} > "${tmpd}"/ghi/a/somefile
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1 -b -V
[ "$?" != "1" ] && echo "compare failed (2)" && exit 1
set -e

###########################
# test update
###########################

# update single file
echo 'update' > "${tmpd}"/def
set +e
cd "${ddpath}" | ${bin} update -f -k -c "${cfg}" -p p1 -b -V f_def
[ "$?" != "0" ] && echo "update failed (1)" && exit 1
set -e
[ ! -e  "${tmpd}"/def ] && echo 'dotfile in FS removed' && exit 1
[ ! -e  "${tmps}"/dotfiles/def ] && echo 'dotfile in dotpath removed' && exit 1

# update single file
set +e
cd "${ddpath}" | ${bin} update -f -k -c "${cfg}" -p p1 -b -V f_abc
[ "$?" != "0" ] && echo "update failed (2)" && exit 1
set -e

# test updated file
[ ! -e "${tmps}"/dotfiles/abc ] && echo "abc does not exist" && exit 1
content=$(cat "${tmps}"/dotfiles/abc)
bcontent=$(echo ${touched} | base64)
[ "${content}" != "${bcontent}" ] && echo "bad content for abc" && exit 1

# update directory
echo ${touched} > "${tmpd}"/ghi/b/newfile
rm -r "${tmpd}"/ghi/c
cd "${ddpath}" | ${bin} update -f -k -c "${cfg}" -p p1 -b -V d_ghi
[ "$?" != "0" ] && echo "update failed" && exit 1

# test updated directory
set +e
tar -tf "${tmps}"/dotfiles/ghi | grep './b/newfile' || (echo "newfile not found in tar" && exit 1)
tar -tf "${tmps}"/dotfiles/ghi | grep './a/dir1/otherfile' || (echo "otherfile not found in tar" && exit 1)
set -e

tmpy=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
clear_on_exit "${tmpy}"
tar -xf "${tmps}"/dotfiles/ghi -C "${tmpy}"
content=$(cat "${tmpy}"/a/somefile)
[ "${content}" != "${touched}" ] && echo "bad content" && exit 1

# check canary dotfile
[ ! -e "${tmps}"/dotfiles/def ] && echo "def not found" && exit 1

echo "OK"
exit 0
