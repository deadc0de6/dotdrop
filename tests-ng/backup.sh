#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6
#
# test for backups
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
    echo "pattern \"${1}\" not found in ${2}"
    exit 1
  fi
}

# the dotfile source
tmps=$(mktemp -d --suffix='-dotdrop-tests-dotpath' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests-dst' || mktemp -d)
tmpw=$(mktemp -d --suffix='-dotdrop-workdir' || mktemp -d)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpw}"

clear_dotpath()
{
  rm -rf "${tmps:?}"/dotfiles/*
}

create_dotpath()
{
  # create the dotfiles in dotpath
  echo "modified" > "${tmps}"/dotfiles/file
  echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/template
  mkdir -p "${tmps}"/dotfiles/dir
  echo "modified" > "${tmps}"/dotfiles/dir/sub
  echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/dir/template
  mkdir -p "${tmps}"/dotfiles/tree
  echo "modified" > "${tmps}"/dotfiles/tree/file
  echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/tree/template
  mkdir -p "${tmps}"/dotfiles/tree/sub
  echo "modified" > "${tmps}"/dotfiles/tree/sub/file
  echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/tree/sub/template
}

clear_fs()
{
  rm -rf "${tmpd:?}"/*
}

create_fs()
{
  # create the existing dotfiles in filesystem
  echo "original" > "${tmpd}"/file
  echo "original" > "${tmpd}"/template
  mkdir -p "${tmpd}"/dir
  echo "original" > "${tmpd}"/dir/sub
  echo "original" > "${tmpd}"/dir/template
  mkdir -p "${tmpd}"/tree
  echo "original" > "${tmpd}"/tree/file
  echo "original" > "${tmpd}"/tree/template
  mkdir -p "${tmpd}"/tree/sub
  echo "original" > "${tmpd}"/tree/sub/file
  echo "original" > "${tmpd}"/tree/sub/template
}

# create the config file
cfg="${tmps}/config.yaml"

# $1: linktype
create_config()
{
  link_default="${1}"
  link_file="${1}"
  link_dir="${1}"
  if [ "${link_default}" = "link_children" ]; then
    link_file="nolink"
  fi
  cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_dotfile_default: ${link_default}
  workdir: ${tmpw}
dotfiles:
  f_file:
    dst: ${tmpd}/file
    src: file
    link: ${link_file}
  f_template:
    dst: ${tmpd}/template
    src: template
    link: ${link_file}
  d_dir:
    dst: ${tmpd}/dir
    src: dir
    link: ${link_dir}
  d_tree:
    dst: ${tmpd}/tree
    src: tree
    link: ${link_dir}
profiles:
  p1:
    dotfiles:
    - f_file
    - f_template
    - d_dir
    - d_tree
_EOF
  #cat ${cfg}
}

# install nolink
pre="link:nolink"
create_config "nolink"
clear_dotpath
clear_fs
create_dotpath
create_fs
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 --verbose

# checks
[ ! -e "${tmpd}"/file.dotdropbak ] && echo "${pre} file backup not found" && exit 1
[ ! -e "${tmpd}"/template.dotdropbak ] && echo "${pre} template backup not found" && exit 1
[ ! -e "${tmpd}"/dir/sub.dotdropbak ] && echo "${pre} dir sub backup not found" && exit 1
[ ! -e "${tmpd}"/dir/template.dotdropbak ] && echo "${pre} dir template backup not found" && exit 1
[ ! -e "${tmpd}"/tree/file.dotdropbak ] && echo "${pre} tree file backup not found" && exit 1
[ ! -e "${tmpd}"/tree/template.dotdropbak ] && echo "${pre} tree template backup not found" && exit 1
[ ! -e "${tmpd}"/tree/sub/file.dotdropbak ] && echo "${pre} tree sub file backup not found" && exit 1
[ ! -e "${tmpd}"/tree/sub/template.dotdropbak ] && echo "${pre} tree sub template backup not found" && exit 1
grep_or_fail original "${tmpd}"/file.dotdropbak
grep_or_fail original "${tmpd}"/template.dotdropbak
grep_or_fail original "${tmpd}"/dir/sub.dotdropbak
grep_or_fail original "${tmpd}"/dir/template.dotdropbak
grep_or_fail original "${tmpd}"/tree/file.dotdropbak
grep_or_fail original "${tmpd}"/tree/template.dotdropbak
grep_or_fail original "${tmpd}"/tree/sub/file.dotdropbak
grep_or_fail original "${tmpd}"/tree/sub/template.dotdropbak
grep_or_fail p1 "${tmpd}"/template
grep_or_fail modified "${tmpd}"/dir/sub
grep_or_fail p1 "${tmpd}"/dir/template
grep_or_fail modified "${tmpd}"/tree/file
grep_or_fail p1 "${tmpd}"/tree/template
grep_or_fail modified "${tmpd}"/tree/sub/file
grep_or_fail p1 "${tmpd}"/tree/sub/template

# install relative
pre="link:relative"
create_config "relative"
clear_dotpath
clear_fs
create_dotpath
create_fs
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 --verbose

# checks
[ ! -e "${tmpd}"/file.dotdropbak ] && echo "${pre} file backup not found" && exit 1
[ ! -e "${tmpd}"/template.dotdropbak ] && echo "${pre} template backup not found" && exit 1
grep_or_fail original "${tmpd}"/file.dotdropbak
grep_or_fail original "${tmpd}"/template.dotdropbak
grep_or_fail p1 "${tmpd}"/template
grep_or_fail modified "${tmpd}"/dir/sub
grep_or_fail p1 "${tmpd}"/dir/template
grep_or_fail modified "${tmpd}"/tree/file
grep_or_fail p1 "${tmpd}"/tree/template
grep_or_fail modified "${tmpd}"/tree/sub/file
grep_or_fail p1 "${tmpd}"/tree/sub/template

# install absolute
pre="link:absolute"
create_config "absolute"
clear_dotpath
clear_fs
create_dotpath
create_fs
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 --verbose

# checks
[ ! -e "${tmpd}"/file.dotdropbak ] && echo "${pre} file backup not found" && exit 1
[ ! -e "${tmpd}"/template.dotdropbak ] && echo "${pre} template backup not found" && exit 1
grep_or_fail original "${tmpd}"/file.dotdropbak
grep_or_fail original "${tmpd}"/template.dotdropbak
grep_or_fail p1 "${tmpd}"/template
grep_or_fail modified "${tmpd}"/dir/sub
grep_or_fail p1 "${tmpd}"/dir/template
grep_or_fail modified "${tmpd}"/tree/file
grep_or_fail p1 "${tmpd}"/tree/template
grep_or_fail modified "${tmpd}"/tree/sub/file
grep_or_fail p1 "${tmpd}"/tree/sub/template

# install link_children
pre="link:link_children"
create_config "link_children"
clear_dotpath
clear_fs
create_dotpath
create_fs
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 --verbose

# checks
[ ! -e "${tmpd}"/file.dotdropbak ] && echo "${pre} file backup not found" && exit 1
[ ! -e "${tmpd}"/template.dotdropbak ] && echo "${pre} template backup not found" && exit 1
[ ! -e "${tmpd}"/dir/sub.dotdropbak ] && echo "${pre} dir sub backup not found" && exit 1
[ ! -e "${tmpd}"/dir/template.dotdropbak ] && echo "${pre} dir template backup not found" && exit 1
[ ! -e "${tmpd}"/tree/file.dotdropbak ] && echo "${pre} tree file backup not found" && exit 1
[ ! -e "${tmpd}"/tree/template.dotdropbak ] && echo "${pre} tree template backup not found" && exit 1
grep_or_fail original "${tmpd}"/file.dotdropbak
grep_or_fail original "${tmpd}"/template.dotdropbak
grep_or_fail original "${tmpd}"/dir/sub.dotdropbak
grep_or_fail original "${tmpd}"/dir/template.dotdropbak
grep_or_fail original "${tmpd}"/tree/file.dotdropbak
grep_or_fail original "${tmpd}"/tree/template.dotdropbak
grep_or_fail p1 "${tmpd}"/template
grep_or_fail modified "${tmpd}"/dir/sub
grep_or_fail p1 "${tmpd}"/dir/template
grep_or_fail modified "${tmpd}"/tree/file
grep_or_fail p1 "${tmpd}"/tree/template
grep_or_fail modified "${tmpd}"/tree/sub/file
grep_or_fail p1 "${tmpd}"/tree/sub/template

echo "OK"
exit 0
