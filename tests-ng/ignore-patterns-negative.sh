#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6
#
# test ignore patterns with negative
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
    - '!*/watch_later/keepme'
    - '!*/watch_later/keepmetoo'
    - '!*/keepmeaswell'
    upignore:
    - '*/watch_later'
    - '!*/watch_later/keepme'
    - '!*/watch_later/keepmetoo'
    - '!*/keepmeaswell'
    instignore:
    - '*/watch_later'
    - '!*/watch_later/keepme'
    - '!*/watch_later/keepmetoo'
    - '!*/keepmeaswell'
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
    - '!*/watch_later/keepme'
    - '!*/watch_later/keepmetoo/*'
    - '!*/keepmeaswell/*'
    upignore:
    - '*/watch_later/*'
    - '!*/watch_later/keepme'
    - '!*/watch_later/keepmetoo/*'
    - '!*/keepmeaswell/*'
    instignore:
    - '*/watch_later/*'
    - '!*/watch_later/keepme'
    - '!*/watch_later/keepmetoo/*'
    - '!*/keepmeaswell/*'
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
    - '!*/watch_later/keepme'
    - '!*/watch_later/keepmetoo'
    - '!*/keepmeaswell'
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
    - '!*/watch_later/keepme'
    - '!*/watch_later/keepmetoo/*'
    - '!*/keepmeaswell/*'
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
  echo "keepme" > "${1}"/mpv/watch_later/keepme
  mkdir -p "${1}"/mpv/watch_later/keepmetoo
  echo "keepmetoo" > "${1}"/mpv/watch_later/keepmetoo/keepmetoo
  mkdir -p "${1}"/mpv/watch_later/keepmeaswell
  echo "keepmeaswell" > "${1}"/mpv/watch_later/keepmeaswell/keepmeaswell
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

[ ! -e "${tmpd}/mpv/watch_later/keepme" ] && echo "install (cfg1) failed" && exit 1
[ ! -d "${tmpd}/mpv/watch_later/keepmetoo" ] && echo "install (cfg1) failed" && exit 1
[ ! -e "${tmpd}/mpv/watch_later/keepmetoo/keepmetoo" ] && echo "install (cfg1) failed" && exit 1
[ ! -e "${tmpd}/mpv/watch_later/keepmeaswell/keepmeaswell" ] && echo "install (cfg1) failed" && exit 1
[ -e "${tmpd}/mpv/watch_later/watch_later_file" ] && echo "install (cfg1) failed" && exit 1

clean_both
create_in_dotpath
cd "${ddpath}" | ${bin} install -f -c "${cfg2}" -p p1 -V

[ ! -e "${tmpd}/mpv/watch_later/keepme" ] && echo "install (cfg2) failed" && exit 1
[ ! -d "${tmpd}/mpv/watch_later/keepmetoo" ] && echo "install (cfg2) failed" && exit 1
[ ! -e "${tmpd}/mpv/watch_later/keepmetoo/keepmetoo" ] && echo "install (cfg2) failed" && exit 1
[ ! -e "${tmpd}/mpv/watch_later/keepmeaswell/keepmeaswell" ] && echo "install (cfg2) failed" && exit 1
[ -e "${tmpd}/mpv/watch_later/watch_later_file" ] && echo "install (cfg2) failed" && exit 1

###################################################
# test update
###################################################
clean_both
create_in_dotpath
create_in_dst
rm -r "${dotpath}/mpv/watch_later"

cd "${ddpath}" | ${bin} update -f -c "${cfg1}" -p p1 -V
[ ! -e "${dotpath}/mpv/watch_later/keepme" ] && echo "update (cfg1) 1 failed" && exit 1
[ ! -d "${dotpath}/mpv/watch_later/keepmetoo" ] && echo "update (cfg1) 2 failed" && exit 1
[ ! -e "${dotpath}/mpv/watch_later/keepmetoo/keepmetoo" ] && echo "update (cfg1) 3 failed" && exit 1
[ ! -e "${dotpath}/mpv/watch_later/keepmeaswell/keepmeaswell" ] && echo "update (cfg1) 4 failed" && exit 1
[ -e "${dotpath}/mpv/watch_later/watch_later_file" ] && echo "update (cfg1) 5 failed" && exit 1

clean_both
create_in_dotpath
create_in_dst
rm -r "${dotpath}/mpv/watch_later"

cd "${ddpath}" | ${bin} update -f -c "${cfg2}" -p p1 -V
[ ! -e "${dotpath}/mpv/watch_later/keepme" ] && echo "update (cfg2) 1 failed" && exit 1
[ ! -d "${dotpath}/mpv/watch_later/keepmetoo" ] && echo "update (cfg2) 2 failed" && exit 1
[ ! -e "${dotpath}/mpv/watch_later/keepmetoo/keepmetoo" ] && echo "update (cfg2) 3 failed" && exit 1
[ ! -e "${dotpath}/mpv/watch_later/keepmeaswell/keepmeaswell" ] && echo "update (cfg2) 4 failed" && exit 1
[ -e "${dotpath}/mpv/watch_later/watch_later_file" ] && echo "update (cfg2) 5 failed" && exit 1

###################################################
# test import
###################################################
clean_both
create_in_dst

cd "${ddpath}" | ${bin} import -f -c "${cfg3}" -p p1 -V "${tmpd}/mpv"
[ ! -e "${dotpath}/${tmpd}/mpv/watch_later/keepme" ] && echo "import (cfg3) 1 failed" && exit 1
[ ! -d "${dotpath}/${tmpd}/mpv/watch_later/keepmetoo" ] && echo "import (cfg3) 2 failed" && exit 1
[ ! -e "${dotpath}/${tmpd}/mpv/watch_later/keepmetoo/keepmetoo" ] && echo "import (cfg3) 3 failed" && exit 1
[ ! -e "${dotpath}/${tmpd}/mpv/watch_later/keepmeaswell/keepmeaswell" ] && echo "import (cfg3) 4 failed" && exit 1
[ -e "${dotpath}/${tmpd}/mpv/watch_later/watch_later_file" ] && echo "import (cfg3) 5 failed" && exit 1

clean_both
create_in_dst

cd "${ddpath}" | ${bin} import -f -c "${cfg4}" -p p1 -V "${tmpd}/mpv"
[ ! -e "${dotpath}/${tmpd}/mpv/watch_later/keepme" ] && echo "import (cfg4) 1 failed" && exit 1
[ ! -d "${dotpath}/${tmpd}/mpv/watch_later/keepmetoo" ] && echo "import (cfg4) 2  failed" && exit 1
[ ! -e "${dotpath}/${tmpd}/mpv/watch_later/keepmetoo/keepmetoo" ] && echo "import (cfg4) 3 failed" && exit 1
[ ! -e "${dotpath}/${tmpd}/mpv/watch_later/keepmeaswell/keepmeaswell" ] && echo "import (cfg4) 4 failed" && exit 1
[ -e "${dotpath}/${tmpd}/mpv/watch_later/watch_later_file" ] && echo "import (cfg4) 5 failed" && exit 1

###################################################
# test compare
###################################################
clean_both
create_in_dst
create_in_dotpath

####
# changed in dotpath
rm "${dotpath}/mpv/watch_later/watch_later_file"
# this should succeed (no diff)
cd "${ddpath}" | ${bin} compare -c "${cfg1}" -p p1 -V

rm -r "${dotpath}/mpv/watch_later"
set +e
# this should fail since it should shows that
# the keepme* are not present
cd "${ddpath}" | ${bin} compare -c "${cfg1}" -p p1 -V && echo "compare cfg1 1 should failed" && exit 1
set -e

clean_both
create_in_dst
create_in_dotpath

####
# changed in dest
rm "${tmpd}/mpv/watch_later/watch_later_file"
# this should succeed (no diff)
cd "${ddpath}" | ${bin} compare -c "${cfg1}" -p p1 -V

rm -r "${tmpd}/mpv/watch_later"
set +e
# this should fail since it should shows that
# the keepme* are not present
cd "${ddpath}" | ${bin} compare -c "${cfg1}" -p p1 -V && echo "compare cfg1 2 should failed" && exit 1
set -e

clean_both
create_in_dst
create_in_dotpath

####
# changed in dotpath
rm "${dotpath}/mpv/watch_later/watch_later_file"
# this should succeed (no diff)
cd "${ddpath}" | ${bin} compare -c "${cfg2}" -p p1 -V

rm -r "${dotpath}/mpv/watch_later"
set +e
# this should fail since it should shows that
# the keepme* are not present
cd "${ddpath}" | ${bin} compare -c "${cfg2}" -p p1 -V && echo "compare cfg2 1 should failed" && exit 1
set -e

clean_both
create_in_dst
create_in_dotpath

####
# changed in dest
rm "${tmpd}/mpv/watch_later/watch_later_file"
# this should succeed (no diff)
cd "${ddpath}" | ${bin} compare -c "${cfg2}" -p p1 -V

rm -r "${tmpd}/mpv/watch_later"
set +e
# this should fail since it should shows that
# the keepme* are not present
cd "${ddpath}" | ${bin} compare -c "${cfg2}" -p p1 -V && echo "compare cfg2 2 should failed" && exit 1
set -e

###################################################

echo "OK"
exit 0
