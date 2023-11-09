#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test pre action execution
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

# $1 pattern
# $2 path
grep_or_fail()
{
  if ! grep "${1}" "${2}" >/dev/null 2>&1; then
    echo "pattern not found in ${2}"
    exit 1
  fi
}

# the action temp
tmpa=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
# the dotfile source
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpa}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
actions:
  pre:
    failpre: "false"
    preaction: echo 'pre' > ${tmpa}/pre
    preaction2: echo 'pre2' > ${tmpa}/pre2
    preaction3: echo 'pre3' > ${tmpa}/pre3
    multiple: echo 'multiple' >> ${tmpa}/multiple
    multiple2: echo 'multiple2' >> ${tmpa}/multiple2
  nakedaction: echo 'naked' > ${tmpa}/naked
  nakedaction2: echo 'naked2' > ${tmpa}/naked2
  nakedaction3: echo 'naked3' > ${tmpa}/naked3
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    actions:
      - preaction
      - nakedaction
  f_fail:
    dst: ${tmpd}/fail
    src: fail
    actions:
      - failpre
  f_link:
    dst: ${tmpd}/link
    src: link
    link: true
    actions:
      - preaction2
      - nakedaction2
  d_dir:
    dst: ${tmpd}/dir
    src: dir
    actions:
      - multiple
  d_dlink:
    dst: ${tmpd}/dlink
    src: dlink
    link: true
    actions:
      - preaction3
      - nakedaction3
      - multiple2
profiles:
  p1:
    dotfiles:
    - f_abc
    - f_link
    - d_dir
    - d_dlink
  p2:
    dotfiles:
    - f_fail
_EOF
#cat ${cfg}

# create the dotfile
echo 'test' > "${tmps}"/dotfiles/abc
echo 'link' > "${tmps}"/dotfiles/link
echo 'fail' > "${tmps}"/dotfiles/fail

mkdir -p "${tmps}"/dotfiles/dir
echo 'test1' > "${tmps}"/dotfiles/dir/file1
echo 'test2' > "${tmps}"/dotfiles/dir/file2

mkdir -p "${tmps}"/dotfiles/dlink
echo 'test3' > "${tmps}"/dotfiles/dlink/dfile1
echo 'test4' > "${tmps}"/dotfiles/dlink/dfile2

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

# checks
[ ! -e "${tmpa}"/pre ] && echo 'pre action not executed' && exit 1
grep_or_fail pre "${tmpa}"/pre
[ ! -e "${tmpa}"/naked ] && echo 'naked action not executed'  && exit 1
grep_or_fail naked "${tmpa}"/naked

[ ! -e "${tmpa}"/multiple ] && echo 'pre action multiple not executed' && exit 1
grep_or_fail multiple "${tmpa}"/multiple
[ "$(wc -l "${tmpa}"/multiple | awk '{print $1}')" -gt "1" ] && echo 'pre action multiple executed twice' && exit 1

[ ! -e "${tmpa}"/pre2 ] && echo 'pre action 2 not executed' && exit 1
grep_or_fail pre2 "${tmpa}"/pre2
[ ! -e "${tmpa}"/naked2 ] && echo 'naked action 2 not executed'  && exit 1
grep_or_fail naked2 "${tmpa}"/naked2

[ ! -e "${tmpa}"/multiple2 ] && echo 'pre action multiple 2 not executed' && exit 1
grep_or_fail multiple2 "${tmpa}"/multiple2
[ "$(wc -l "${tmpa}"/multiple2 | awk '{print $1}')" -gt "1" ] && echo 'pre action multiple 2 executed twice' && exit 1
[ ! -e "${tmpa}"/naked3 ] && echo 'naked action 3 not executed'  && exit 1
grep_or_fail naked3 "${tmpa}"/naked3

# remove the pre action result and re-install
rm "${tmpa}"/pre
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V
[ -e "${tmpa}"/pre ] && echo "pre exists" && exit 1

# ensure failing actions make the installation fail
# install
set +e
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p2 -V
set -e
[ -e "${tmpd}"/fail ] && echo "fail exists" && exit 1

echo "OK"
exit 0
