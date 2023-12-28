#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test ignore patterns
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
cfg4="${tmps}/config4.yaml"

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
    - '*/watch_later'
    upignore:
    - '*/watch_later'
    instignore:
    - '*/watch_later'
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
dotfiles:
  d_mpv:
    src: mpv
    dst: ${tmpd}/mpv
    cmpignore:
    - '*/watch_later/*'
    upignore:
    - '*/watch_later/*'
    instignore:
    - '*/watch_later/*'
profiles:
  p1:
    dotfiles:
    - d_mpv
_EOF

cat > "${cfg3}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  ignoreempty: true
  impignore:
    - '*/watch_later'
dotfiles:
profiles:
_EOF

cat > "${cfg4}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  ignoreempty: true
  impignore:
    - '*/watch_later/*'
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
  echo "watch_later" > "${1}"/mpv/watch_later/watch_later_file
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

[ -d "${tmpd}/mpv/watch_later" ] && echo "install (cfg1) failed" && exit 1

clean_both
create_in_dotpath
cd "${ddpath}" | ${bin} install -f -c "${cfg2}" -p p1 -V

[ -d "${tmpd}/mpv/watch_later" ] && echo "install (cfg2) failed" && exit 1

###################################################
# test update
###################################################
clean_both
create_in_dotpath
create_in_dst
echo newfile "${tmpd}/mpv/watch_later/newfile"
[ ! -e "${dotpath}/mpv/watch_later" ] && echo "1 does not exist!" && exit 1
rm -r "${dotpath}/mpv/watch_later"

cd "${ddpath}" | ${bin} update -f -c "${cfg1}" -p p1 -V
[ -d "${dotpath}/mpv/watch_later" ] && echo "update (cfg1) failed" && exit 1
[ -e "${dotpath}/mpv/watch_later/newfile" ] && echo "update (cfg1) failed - new file" && exit 1

clean_both
create_in_dotpath
create_in_dst
echo newfile "${tmpd}/mpv/watch_later/newfile"
[ ! -e "${dotpath}/mpv/watch_later" ] && echo "2 does not exist!" && exit 1
rm -r "${dotpath}/mpv/watch_later"

cd "${ddpath}" | ${bin} update -f -c "${cfg2}" -p p1 -V
[ -d "${dotpath}/mpv/watch_later" ] && echo "update (cfg2) failed" && exit 1
[ -e "${dotpath}/mpv/watch_later/newfile" ] && echo "update (cfg2) failed - new file" && exit 1

###################################################
# test import
###################################################
clean_both
create_in_dst

cd "${ddpath}" | ${bin} import -f -c "${cfg3}" -p p1 -V "${tmpd}/mpv"
[ -d "${dotpath}/${tmpd}/mpv/watch_later" ] && echo "import (cfg3) failed" && exit 1
[ ! -e "${dotpath}/${tmpd}/mpv/file" ] && echo "import (cfg3) failed - file" && exit 1

clean_both
create_in_dst

cd "${ddpath}" | ${bin} import -f -c "${cfg4}" -p p1 -V "${tmpd}/mpv"
[ -d "${dotpath}/${tmpd}/mpv/watch_later" ] && echo "import (cfg4) failed" && exit 1
[ ! -e "${dotpath}/${tmpd}/mpv/file" ] && echo "import (cfg4) failed - file" && exit 1

###################################################
# test compare
###################################################
clean_both
create_in_dst
create_in_dotpath

[ ! -e "${dotpath}/mpv/watch_later" ] && echo "3 does not exist!" && exit 1
rm -r "${dotpath}/mpv/watch_later"
cd "${ddpath}" | ${bin} compare -c "${cfg1}" -p p1 -V

clean_both
create_in_dst
create_in_dotpath

[ ! -e "${tmpd}/mpv/watch_later" ] && echo "4 does not exist!" && exit 1
rm -r "${tmpd}/mpv/watch_later"
cd "${ddpath}" | ${bin} compare -c "${cfg1}" -p p1 -V

clean_both
create_in_dst
create_in_dotpath

[ ! -e "${dotpath}/mpv/watch_later" ] && echo "5 does not exist!" && exit 1
rm -r "${dotpath}/mpv/watch_later"
cd "${ddpath}" | ${bin} compare -c "${cfg2}" -p p1 -V

clean_both
create_in_dst
create_in_dotpath

[ ! -e "${tmpd}/mpv/watch_later" ] && echo "6 does not exist!" && exit 1
rm -r "${tmpd}/mpv/watch_later"
cd "${ddpath}" | ${bin} compare -c "${cfg2}" -p p1 -V

###################################################

echo "OK"
exit 0
