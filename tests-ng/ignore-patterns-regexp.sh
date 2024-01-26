#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2024, deadc0de6
#
# test ignore patterns with regexp
# returns 1 in case of error
# see #418
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
dotpath="${tmps}"/dotfiles
mkdir -p "${dotpath}"
#echo "dotfile source: ${tmps}"
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg1="${tmps}/config1.yaml"
cfg2="${tmps}/config2.yaml"
cfg3="${tmps}/config3.yaml"

cat > "${cfg1}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  ignoreempty: true
dotfiles:
  d_adir:
    src: adir
    dst: ${tmpd}/adir
    cmpignore:
    - '!Custom Dictionary.txt'
    - '[a-zA-Z0-9]*'
profiles:
  p1:
    dotfiles:
    - d_adir
_EOF

cat > "${cfg2}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  ignoreempty: true
dotfiles:
  d_adir:
    src: adir
    dst: ${tmpd}/adir
    cmpignore:
    - '!Custom Dictionary.txt'
    - '[a-zA-Z0-9\ ]*'
profiles:
  p1:
    dotfiles:
    - d_adir
_EOF

cat > "${cfg3}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  ignoreempty: true
dotfiles:
  d_adir:
    src: adir
    dst: ${tmpd}/adir
    cmpignore:
    - "*"
    - '!Custom Dictionary.txt'
profiles:
  p1:
    dotfiles:
    - d_adir
_EOF

# list from https://github.com/deadc0de6/dotdrop/issues/431
mkdir -p "${dotpath}"/adir
mkdir -p "${tmpd}"/adir
# dotpath
mkdir -p "${dotpath}/adir"
echo "myfile" > "${dotpath}/adir/myfile"
# directories
mkdir -p "${tmpd}/adir/blob_storage"
mkdir -p "${tmpd}/adir/Cache"
mkdir -p "${tmpd}/adir/Code\ Cache"
mkdir -p "${tmpd}/adir/Crashpad"
mkdir -p "${tmpd}/adir/databases"
mkdir -p "${tmpd}/adir/DawnCache"
mkdir -p "${tmpd}/adir/Dictionaries"
mkdir -p "${tmpd}/adir/GPUCache"
mkdir -p "${tmpd}/adir/IndexedDB"
mkdir -p "${tmpd}/adir/Local\ Storage"
mkdir -p "${tmpd}/adir/Obsidian\ Sandbox"
mkdir -p "${tmpd}/adir/Service\ Worker"
mkdir -p "${tmpd}/adir/Session\ Storage"
mkdir -p "${tmpd}/adir/shared_proto_db"
mkdir -p "${tmpd}/adir/VideoDecodeStats"
mkdir -p "${tmpd}/adir/WebStorage"
touch "${tmpd}/adir/blob_storage/file"
touch "${tmpd}/adir/Cache/file"
touch "${tmpd}/adir/Code\ Cache/file"
touch "${tmpd}/adir/Crashpad/file"
touch "${tmpd}/adir/databases/file"
touch "${tmpd}/adir/DawnCache/file"
touch "${tmpd}/adir/Dictionaries/file"
touch "${tmpd}/adir/GPUCache/file"
touch "${tmpd}/adir/IndexedDB/file"
touch "${tmpd}/adir/Local\ Storage/file"
touch "${tmpd}/adir/Obsidian\ Sandbox/file"
touch "${tmpd}/adir/Service\ Worker/file"
touch "${tmpd}/adir/Session\ Storage/file"
touch "${tmpd}/adir/shared_proto_db/file"
touch "${tmpd}/adir/VideoDecodeStats/file"
touch "${tmpd}/adir/WebStorage/file"
# files
echo 'afile' > "${tmpd}/adir/1853510a538d0a01.json"
echo 'afile' > "${tmpd}/adir/Cookies"
echo 'afile' > "${tmpd}/adir/Cookies-journal"
echo 'afile' > "${tmpd}/adir/Custom\ Dictionary.txt'"
echo 'afile' > "${tmpd}/adir/Custom\ Dictionary.txt.backup"
echo 'afile' > "${tmpd}/adir/id"
echo 'afile' > "${tmpd}/adir/Network\ Persistent\ State"
echo 'afile' > "${tmpd}/adir/obsidian.json"
echo 'afile' > "${tmpd}/adir/obsidian.log"
echo 'afile' > "${tmpd}/adir/Preferences"
echo 'afile' > "${tmpd}/adir/SingletonCookie"
echo 'afile' > "${tmpd}/adir/SingletonLock"
echo 'afile' > "${tmpd}/adir/SingletonSocket"
echo 'afile' > "${tmpd}/adir/TransportSecurity"

###################################################
# install
###################################################
cd "${ddpath}" | ${bin} install -f -c "${cfg1}" -p p1 -V
[ ! -d "${tmpd}/adir" ] && echo "install dir (cfg1) failed" && exit 1
[ ! -e "${tmpd}/adir/myfile" ] && echo "install file (cfg1) failed" && exit 1

###################################################
# compare cfg1
###################################################
cd "${ddpath}" | ${bin} compare -c "${cfg1}" -p p1 -V

###################################################
# compare cfg2
###################################################
cd "${ddpath}" | ${bin} compare -c "${cfg2}" -p p1 -V

###################################################
# compare cfg3
###################################################
cd "${ddpath}" | ${bin} compare -c "${cfg3}" -p p1 -V

echo "OK"
exit 0
