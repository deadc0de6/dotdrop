#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2024, deadc0de6
#
# test ignore patterns and especially that if
# the directory content is ignored, so is the directory itself
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
tmps=$(mktemp -d --suffix='-dotdrop-dotpath' || mktemp -d)
dotpath="${tmps}"/dotfiles
mkdir -p "${dotpath}"
#echo "dotfile source: ${tmps}"
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-fs' || mktemp -d)
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg1="${tmps}/config1.yaml"
cfg2="${tmps}/config2.yaml"

cat > "${cfg1}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  ignoreempty: true
dotfiles:
  d_mpv:
    src: mpv
    dst: ${tmpd}/mpv
    cmpignore:
    - '*/watch_later/x'
    upignore:
    - '*/watch_later/x'
    instignore:
    - '*/watch_later/x'
profiles:
  p1:
    dotfiles:
    - d_mpv
_EOF

cat > "${cfg2}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  ignoreempty: true
  impignore:
    - '*/watch_later/x'
dotfiles:
profiles:
_EOF

clean_both()
{
  rm -rf "${dotpath}/mpv"
  rm -rf "${tmpd}/mpv"
}

# $1 parent
create_hierarchy()
{
  mkdir -p "${1}"/mpv
  echo "file" > "${1}"/mpv/file
  mkdir -p "${1}"/mpv/dir1
  echo "file2" > "${1}"/mpv/dir1/file
  mkdir -p "${1}"/mpv/watch_later
  echo "watch_later" > "${1}"/mpv/watch_later/x
}

create_in_dotpath()
{
  create_hierarchy "${dotpath}"
}

create_in_dst()
{
  create_hierarchy "${tmpd}"
}

###################################################
# test install
###################################################
clean_both
create_in_dotpath
cd "${ddpath}" | ${bin} install -f -c "${cfg1}" -p p1 -V
[ -d "${tmpd}/mpv/watch_later" ] && echo "install failed" && exit 1

###################################################
# test update
###################################################
clean_both
create_in_dotpath
create_in_dst

# modify
echo newfile > "${tmpd}/mpv/new"
rm -rf "${dotpath}/mpv/watch_later"

cd "${ddpath}" | ${bin} update -f -c "${cfg1}" -p p1 -V
[ -d "${dotpath}/mpv/watch_later" ] && echo "update failed - watch_later created" && exit 1
[ -e "${dotpath}/mpv/watch_later/x" ] && echo "update failed - x added" && exit 1
[ ! -e "${dotpath}/mpv/new" ] && echo "update failed - no new file" && exit 1

###################################################
# test import
###################################################
clean_both
create_in_dst

cd "${ddpath}" | ${bin} import -f -c "${cfg2}" -p p1 -V "${tmpd}/mpv"
[ -d "${dotpath}/${tmpd}/mpv/watch_later" ] && echo "import failed" && exit 1
[ ! -e "${dotpath}/${tmpd}/mpv/file" ] && echo "import failed - file" && exit 1

###################################################
# test compare
###################################################
clean_both
create_in_dst
create_in_dotpath

rm -r "${dotpath}/mpv/watch_later"
cd "${ddpath}" | ${bin} compare -c "${cfg1}" -p p1 -V

###################################################

echo "OK"
exit 0
