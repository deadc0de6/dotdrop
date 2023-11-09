#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2020, deadc0de6
#
# test notemplate
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
#echo "dotfile source: ${tmps}"
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"

# globally
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  template_dotfile_default: false
dotfiles:
  f_f1:
    dst: ${tmpd}/f1
    src: f1
  d_d1:
    dst: ${tmpd}/dir1
    src: dir1
  d_d2:
    dst: ${tmpd}/dir2
    src: dir2
    link: link
  d_d3:
    dst: ${tmpd}/dir3
    src: dir3
    link: link_children
  f_fl:
    dst: ${tmpd}/fl
    src: fl
    link: link
  f_fn:
    dst: ${tmpd}/fn
    src: fn
    template: true
profiles:
  p1:
    dotfiles:
    - f_f1
    - d_d1
    - d_d2
    - d_d3
    - f_fl
    - f_fn
_EOF
#cat ${cfg}

# create the dotfile
echo "before" > "${tmps}"/dotfiles/f1
echo "{#@@ should not be stripped @@#}" >> "${tmps}"/dotfiles/f1
echo "{{@@ header() @@}}" >> "${tmps}"/dotfiles/f1
echo "after" >> "${tmps}"/dotfiles/f1

# create the directory
mkdir -p "${tmps}"/dotfiles/dir1/d1
echo "{{@@ header() @@}}" > "${tmps}"/dotfiles/dir1/d1/f2

# create the linked directory
mkdir -p "${tmps}"/dotfiles/dir2/d1
echo "{{@@ header() @@}}" > "${tmps}"/dotfiles/dir2/d1/f2

# create the link_children directory
mkdir -p "${tmps}"/dotfiles/dir3/{s1,s2,s3}
echo "{{@@ header() @@}}" > "${tmps}"/dotfiles/dir3/s1/f1
echo "{{@@ header() @@}}" > "${tmps}"/dotfiles/dir3/s2/f2

# create the linked dotfile
echo "{{@@ header() @@}}" > "${tmps}"/dotfiles/fl

# create the normal dotfile
echo "before" > "${tmps}"/dotfiles/fn
echo "{#@@ should be stripped @@#}" >> "${tmps}"/dotfiles/fn
echo "after" >> "${tmps}"/dotfiles/fn

# install
echo "installing"
cd "${ddpath}" | ${bin} install -f --showdiff -c "${cfg}" -p p1 -V
echo "comparing"
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1 -V

# simple file
echo "doing globally"
echo "* test simple file"
[ ! -e "${tmpd}"/f1 ] && echo 'not installed1' && exit 1
grep 'header' "${tmpd}"/f1 || (echo "header stripped" && exit 1)
grep 'should not be stripped' "${tmpd}"/f1 || (echo "comment stripped" && exit 1)

# directory
echo "* test directory"
[ ! -d "${tmpd}"/dir1 ] && echo 'not installed1' && exit 1
[ ! -d "${tmpd}"/dir1/d1 ] && echo 'not installed2' && exit 1
[ ! -e "${tmpd}"/dir1/d1/f2 ] && echo 'not installed3' && exit 1
grep 'header' "${tmpd}"/dir1/d1/f2 || (echo "header stripped" && exit 1)

# linked directory
echo "* test linked directory"
[ ! -h "${tmpd}"/dir2 ] && echo 'not installed1' && exit 1
[ ! -d "${tmpd}"/dir2/d1 ] && echo 'not installed2' && exit 1
[ ! -e "${tmpd}"/dir2/d1/f2 ] && echo 'not installed3' && exit 1
grep 'header' "${tmpd}"/dir2/d1/f2 || (echo "header stripped" && exit 1)

# children_link directory
echo "* test link_children directory"
[ ! -d "${tmpd}"/dir3 ] && echo 'not installed1' && exit 1
[ ! -h "${tmpd}"/dir3/s1 ] && echo 'not installed2' && exit 1
[ ! -h "${tmpd}"/dir3/s2 ] && echo 'not installed3' && exit 1
[ ! -h "${tmpd}"/dir3/s3 ] && echo 'not installed4' && exit 1
[ ! -e "${tmpd}"/dir3/s1/f1 ] && echo 'not installed5' && exit 1
[ ! -e "${tmpd}"/dir3/s2/f2 ] && echo 'not installed6' && exit 1
grep 'header' "${tmpd}"/dir3/s1/f1 || (echo "header stripped" && exit 1)
grep 'header' "${tmpd}"/dir3/s2/f2 || (echo "header stripped" && exit 1)

# linked file
echo "* test linked file"
[ ! -h "${tmpd}"/fl ] && echo 'not installed' && exit 1
grep 'header' "${tmpd}"/f1 || (echo "header stripped" && exit 1)

# normal dotfile
echo "* normal dotfile"
[ ! -e "${tmpd}"/fn ] && echo 'not installed' && exit 1
grep 'should be stripped' "${tmpd}"/fn && echo "not templated" && exit 1

# test backup done
echo "before" > "${tmps}"/dotfiles/f1
cd "${ddpath}" | ${bin} install -f --showdiff -c "${cfg}" -p p1 -V
[ ! -e "${tmpd}"/f1.dotdropbak ] && echo "backup not done" && exit 1

# re-create the dotfile
echo "before" > "${tmps}"/dotfiles/f1
echo "{#@@ should not be stripped @@#}" >> "${tmps}"/dotfiles/f1
echo "{{@@ header() @@}}" >> "${tmps}"/dotfiles/f1
echo "after" >> "${tmps}"/dotfiles/f1

# through the dotfile
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  template_dotfile_default: true
dotfiles:
  f_f1:
    dst: ${tmpd}/f1
    src: f1
    template: false
  d_d1:
    dst: ${tmpd}/dir1
    src: dir1
    template: false
  d_d2:
    dst: ${tmpd}/dir2
    src: dir2
    link: link
    template: false
  d_d3:
    dst: ${tmpd}/dir3
    src: dir3
    link: link_children
    template: false
  f_fl:
    dst: ${tmpd}/fl
    src: fl
    link: link
    template: false
  f_fn:
    dst: ${tmpd}/fn
    src: fn
profiles:
  p1:
    dotfiles:
    - f_f1
    - d_d1
    - d_d2
    - d_d3
    - f_fl
    - f_fn
_EOF
#cat ${cfg}

# clean destination
rm -rf "${tmpd:?}"/*

# install
cd "${ddpath}" | ${bin} install -f --showdiff -c "${cfg}" -p p1 -V
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1 -V

# simple file
echo "doing specifically"
echo "* test simple file"
[ ! -e "${tmpd}"/f1 ] && echo 'not installed1' && exit 1
grep 'header' "${tmpd}"/f1 || (echo "header stripped" && exit 1)
grep 'should not be stripped' "${tmpd}"/f1 || (echo "comment stripped" && exit 1)

# directory
echo "* test directory"
[ ! -d "${tmpd}"/dir1 ] && echo 'not installed1' && exit 1
[ ! -d "${tmpd}"/dir1/d1 ] && echo 'not installed2' && exit 1
[ ! -e "${tmpd}"/dir1/d1/f2 ] && echo 'not installed3' && exit 1
grep 'header' "${tmpd}"/dir1/d1/f2 || (echo "header stripped" && exit 1)

# linked directory
echo "* test linked directory"
[ ! -h "${tmpd}"/dir2 ] && echo 'not installed1' && exit 1
[ ! -d "${tmpd}"/dir2/d1 ] && echo 'not installed2' && exit 1
[ ! -e "${tmpd}"/dir2/d1/f2 ] && echo 'not installed3' && exit 1
grep 'header' "${tmpd}"/dir2/d1/f2 || (echo "header stripped" && exit 1)

# children_link directory
echo "* test link_children directory"
[ ! -d "${tmpd}"/dir3 ] && echo 'not installed1' && exit 1
[ ! -h "${tmpd}"/dir3/s1 ] && echo 'not installed2' && exit 1
[ ! -h "${tmpd}"/dir3/s2 ] && echo 'not installed3' && exit 1
[ ! -h "${tmpd}"/dir3/s3 ] && echo 'not installed4' && exit 1
[ ! -e "${tmpd}"/dir3/s1/f1 ] && echo 'not installed5' && exit 1
[ ! -e "${tmpd}"/dir3/s2/f2 ] && echo 'not installed6' && exit 1
grep 'header' "${tmpd}"/dir3/s1/f1 || (echo "header stripped" && exit 1)
grep 'header' "${tmpd}"/dir3/s2/f2 || (echo "header stripped" && exit 1)

# linked file
echo "* test linked file"
[ ! -h "${tmpd}"/fl ] && echo 'not installed' && exit 1
grep 'header' "${tmpd}"/f1 || (echo "header stripped" && exit 1)

# normal dotfile
echo "* normal dotfile"
[ ! -e "${tmpd}"/fn ] && echo 'not installed' && exit 1
grep 'should not be stripped' "${tmpd}"/fn && echo "no templated" && exit 1

echo "OK"
exit 0
