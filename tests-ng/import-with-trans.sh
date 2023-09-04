#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6
#
# test transformations for import
# returns 1 in case of error
#

## start-cookie
set -e
cur=$(cd "$(dirname "${0}")" && pwd)
ddpath="${cur}/../"
export PYTHONPATH="${ddpath}:${PYTHONPATH}"
altbin="python3 -m dotdrop.dotdrop"
if hash coverage 2>/dev/null; then
  altbin="coverage run -p --source=dotdrop -m dotdrop.dotdrop"
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

cat > "${cfg}" << _EOF
trans_read:
  base64: "cat {0} | base64 -d > {1}"
  decompress: "mkdir -p {1} && tar -xf {0} -C {1}"
  decrypt: "echo {{@@ profile @@}} | gpg -q --batch --yes --passphrase-fd 0 --no-tty -d {0} > {1}"
trans_write:
  base64: "cat {0} | base64 > {1}"
  compress: "tar -cf {1} -C {0} ."
  encrypt: "echo {{@@ profile @@}} | gpg -q --batch --yes --passphrase-fd 0 --no-tty -o {1} -c {0}"
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF
#cat ${cfg}

# tokens
token="test-base64"
tokend="compressed archive"
tokenenc="encrypted"

# create the dotfiles
echo ${token} > "${tmpd}"/abc
mkdir -p "${tmpd}"/def/a
echo "${tokend}" > "${tmpd}"/def/a/file
echo ${tokenenc} > "${tmpd}"/ghi

###########################
# test import
###########################

echo "[+] run import"
# import file (to base64)
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -b -V --transw=base64 --transr=base64 "${tmpd}"/abc
# import directory (to compress)
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -b -V --transw=compress --transr=decompress "${tmpd}"/def
# import file (to encrypt)
#cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -b -V --transw=encrypt --transr=decrypt "${tmpd}"/ghi

# check file imported in dotpath
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/abc ] && echo "abc does not exist" && exit 1
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/def ] && echo "def does not exist" && exit 1
#[ ! -e "${tmps}"/dotfiles/"${tmpd}"/ghi ] && echo "ghi does not exist" && exit 1

# check content in dotpath
echo "checking content"
file "${tmps}"/dotfiles/"${tmpd}"/abc | grep -i 'text'
cat "${tmpd}"/abc | base64 > "${tmps}"/test-abc
diff "${tmps}"/dotfiles/"${tmpd}"/abc "${tmps}"/test-abc

file "${tmps}"/dotfiles/"${tmpd}"/def | grep -i 'tar'
tar -cf "${tmps}"/test-def -C "${tmpd}"/def .
diff "${tmps}"/dotfiles/"${tmpd}"/def "${tmps}"/test-def

file "${tmps}"/dotfiles/"${tmpd}"/ghi | grep -i 'gpg symmetrically encrypted data\|PGP symmetric key encrypted data'
echo p1 | gpg -q --batch --yes --passphrase-fd 0 --no-tty -d "${tmps}"/dotfiles/"${tmpd}"/ghi > "${tmps}"/test-ghi
diff "${tmps}"/test-ghi "${tmpd}"/ghi

# check is imported in config
echo "checking imported in config"
cd "${ddpath}" | ${bin} -p p1 -c "${cfg}" files
cd "${ddpath}" | ${bin} -p p1 -c "${cfg}" files | grep '^f_abc'
cd "${ddpath}" | ${bin} -p p1 -c "${cfg}" files | grep '^d_def'
#cd "${ddpath}" | ${bin} -p p1 -c "${cfg}" files | grep '^f_ghi'

# check has trans_write and trans_read in config
echo "checking trans_write is set in config"
echo "--------------"
cat "${cfg}"
echo "--------------"
cat "${cfg}" | grep -A 4 'f_abc:' | grep 'trans_write: base64'
cat "${cfg}" | grep -A 4 'd_def:' | grep 'trans_write: compress'
#cat "${cfg}" | grep -A 4 'f_ghi:' | grep 'trans_write: encrypt'

cat "${cfg}" | grep -A 4 'f_abc:' | grep 'trans_read: base64'
cat "${cfg}" | grep -A 4 'd_def:' | grep 'trans_read: decompress'
#cat "${cfg}" | grep -A 4 'f_ghi:' | grep 'trans_read: decrypt'

# install these
echo "install and check"
rm "${tmpd}"/abc
rm -r "${tmpd}"/def
#rm "${tmpd}"/ghi

cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b -V

# test exist
echo "check exist"
[ ! -e "${tmpd}"/abc ] && exit 1
[ ! -d "${tmpd}"/def/a ] && exit 1
[ ! -e "${tmpd}"/def/a/file ] && exit 1
#[ ! -e "${tmpd}"/ghi ] && exit 1

# test content
echo "check content"
cat "${tmpd}"/abc
cat "${tmpd}"/abc | grep "${token}"
cat "${tmpd}"/def/a/file
cat "${tmpd}"/def/a/file | grep "${tokend}"
#cat "${tmpd}"/ghi | grep "${tokenenc}"

echo "OK"
exit 0
