#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2024, deadc0de6
#
# test with user provided key
# --dkey
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
echo "file1" > "${tmpd}"/file1

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
#cat ${cfg}

# import
dkey="myfile1"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V --dkey "${dkey}" "${tmpd}"/file1
cat "${cfg}"

# test
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/file1 ] && echo "not imported in dotpath" && exit 1
cat "${cfg}" | grep "${dkey}:" &>/dev/null || ( echo "bad key 1" && exit 1 )

# import 2 files
echo "firstfile" > "${tmpd}"/firstfile
echo "secondfile" > "${tmpd}"/secondfile

dkey="nfile"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V --dkey "${dkey}" "${tmpd}"/firstfile "${tmpd}"/secondfile
cat "${cfg}"

# test
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/firstfile ] && echo "not imported in dotpath" && exit 1
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/secondfile ] && echo "not imported in dotpath" && exit 1
cat "${cfg}" | grep "${dkey}:" &>/dev/null || ( echo "bad key 2a" && exit 1 )
cat "${cfg}" | grep "${dkey}_1:" &>/dev/null || ( echo "bad key 2b" && exit 1 )

# import 2 files with bad chars
echo "file-1.1" > "${tmpd}"/file-1.1
echo "file-2.2" > "${tmpd}"/file-2.2

dkey=".bad-key.1 2"
dkey_clean="bad-key.1-2"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V --dkey "${dkey}" "${tmpd}"/file-1.1 "${tmpd}"/file-2.2
cat "${cfg}"

# test
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/file-1.1 ] && echo "not imported in dotpath" && exit 1
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/file-2.2 ] && echo "not imported in dotpath" && exit 1
cat "${cfg}" | grep "${dkey_clean}:" &>/dev/null || ( echo "bad key 3a" && exit 1 )
cat "${cfg}" | grep "${dkey_clean}_1:" &>/dev/null || ( echo "bad key 3b" && exit 1 )

# re-import
echo "lastfile" > "${tmpd}"/lastfile

dkey="nfile"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V --dkey "${dkey}" "${tmpd}"/lastfile 
cat "${cfg}"

# test
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/lastfile ] && echo "not imported in dotpath" && exit 1
cat "${cfg}" | grep "${dkey}_2:" &>/dev/null || ( echo "bad key 4" && exit 1 )

# bad char
echo "firstfile" > "${tmpd}"/badchar

dkey=".key@#\$ˆ&*()abc0032"
dkey_clean="key_abc0032"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V --dkey "${dkey}" "${tmpd}"/badchar
cat "${cfg}"

# test
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/badchar ] && echo "not imported in dotpath" && exit 1
cat "${cfg}" | grep "${dkey_clean}:" &>/dev/null || ( echo "bad key 5" && exit 1 )

echo "OK"
exit 0
