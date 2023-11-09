#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2020, deadc0de6
#
# test tmeplate link value
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

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
variables:
  link_true: "link"
  link_false: "nolink"
  link_children_val: "link_children"
dynvariables:
  dyn_link_true: "echo link"
  dyn_link_false: "echo nolink"
  dyn_link_children_val: "echo link_children"
dotfiles:
  f_a:
    dst: ${tmpd}/a
    src: a
    link: "{{@@ link_false @@}}"
  f_b:
    dst: ${tmpd}/b
    src: b
    link: "{{@@ link_true @@}}"
  f_c:
    dst: ${tmpd}/c
    src: c
    link: "{{@@ dyn_link_false @@}}"
  f_d:
    dst: ${tmpd}/d
    src: d
    link: "{{@@ dyn_link_true @@}}"
  f_e:
    dst: ${tmpd}/e
    src: e
    link: "{{@@ link_children_val @@}}"
  f_f:
    dst: ${tmpd}/f
    src: f
    link: "{{@@ dyn_link_children_val @@}}"
  f_not:
    dst: ${tmpd}/n
    src: n
    link: "{{@@ link_true @@}}"
profiles:
  p1:
    dotfiles:
    - f_a
    - f_b
    - f_c
    - f_d
    - f_e
    - f_f
_EOF
#cat ${cfg}

# create the dotfile
echo "filea" > "${tmps}"/dotfiles/a
echo "fileb" > "${tmps}"/dotfiles/b
echo "filec" > "${tmps}"/dotfiles/c
echo "filed" > "${tmps}"/dotfiles/d
mkdir -p "${tmps}"/dotfiles/e/{1,2,3}
echo filee > "${tmps}"/dotfiles/e/1/file
echo filee > "${tmps}"/dotfiles/e/2/file
echo filee > "${tmps}"/dotfiles/e/3/file
mkdir -p "${tmps}"/dotfiles/f/{1,2,3}
echo filee > "${tmps}"/dotfiles/f/1/file
echo filee > "${tmps}"/dotfiles/f/2/file
echo filee > "${tmps}"/dotfiles/f/3/file

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b -V

# checks
[ ! -e "${tmpd}"/a ] && echo "[ERROR] dotfile a not linked" && exit 1
[ ! -h "${tmpd}"/b ] && echo "[ERROR] dotfile b linked" && exit 1
[ ! -e "${tmpd}"/c ] && echo "[ERROR] dotfile c not linked" && exit 1
[ ! -h "${tmpd}"/d ] && echo "[ERROR] dotfile d linked" && exit 1

# link_children
[ ! -d "${tmpd}"/e ] && echo "[ERROR] dir e does not exist" && exit 1
[ ! -h "${tmpd}"/e/1 ] && echo "[ERROR] children e/1 not linked" && exit 1
[ ! -h "${tmpd}"/e/2 ] && echo "[ERROR] children e/2 not linked" && exit 1
[ ! -h "${tmpd}"/e/3 ] && echo "[ERROR] children e/3 not linked" && exit 1

[ ! -d "${tmpd}"/f ] && echo "[ERROR] dir f does not exist" && exit 1
[ ! -h "${tmpd}"/f/1 ] && echo "[ERROR] children f/1 not linked" && exit 1
[ ! -h "${tmpd}"/f/2 ] && echo "[ERROR] children f/2 not linked" && exit 1
[ ! -h "${tmpd}"/f/3 ] && echo "[ERROR] children f/3 not linked" && exit 1

echo "OK"
exit 0
