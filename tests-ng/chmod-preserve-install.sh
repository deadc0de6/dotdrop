#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6
#
# test chmod preserve on install
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

# $1 path
# $2 rights
has_rights()
{
  echo "testing ${1} is ${2}"
  [ ! -e "$1" ] && echo "$(basename "$1") does not exist" && exit 1
  local mode
  mode=$(stat -L -c '%a' "$1")
  [ "${mode}" != "$2" ] && echo "bad mode for $(basename "$1") (${mode} VS expected ${2})" && exit 1
  true
}

# test $1 path has same right than $2
is_same_as()
{
  echo "testing ${1} has same rights than ${2}"
  [ ! -e "$1" ] && echo "$(basename "$1") does not exist" && exit 1
  [ ! -e "$2" ] && echo "$(basename "$2") does not exist" && exit 1

  local mode1
  mode1=$(stat -L -c '%a' "$1")
  echo "$1: ${mode1}"
  local mode2
  mode2=$(stat -L -c '%a' "$2")
  echo "$2: ${mode2}"

  [ "${mode1}" != "${mode2}" ] && echo "$(basename "$1") (${mode1}) does not have same mode as $(basename "$2") (${mode2})" && exit 1
  true
}

get_default_file_mode()
{
  u=$(umask)
  # shellcheck disable=SC2001
  u=$(echo "${u}" | sed 's/^0*//')
  v=$((666 - u))
  echo "${v}"
}

get_default_dir_mode()
{
  u=$(umask)
  # shellcheck disable=SC2001
  u=$(echo "${u}" | sed 's/^0*//')
  v=$((777 - u))
  echo "${v}"
}

# the dotfile source
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"

##
# non existing files
##

# file
echo 'f777' > "${tmps}"/dotfiles/f777
chmod 700 "${tmps}"/dotfiles/f777

# link
echo 'link' > "${tmps}"/dotfiles/link
chmod 700 "${tmps}"/dotfiles/link

# directory
mkdir -p "${tmps}"/dotfiles/dir
echo "f1" > "${tmps}"/dotfiles/dir/f1
chmod 700 "${tmps}"/dotfiles/dir
chmod 700 "${tmps}"/dotfiles/dir/f1

# template
echo '{{@@ profile @@}}' > "${tmps}"/dotfiles/template
chmod 700 "${tmps}"/dotfiles/template

# link template
echo '{{@@ profile @@}}' > "${tmps}"/dotfiles/link-template
chmod 700 "${tmps}"/dotfiles/link-template

##
# existing files
##

# file
echo "exists-original" > "${tmps}"/dotfiles/exists
chmod 644 "${tmps}"/dotfiles/exists
echo "exists" > "${tmpd}"/exists
chmod 700 "${tmpd}"/exists

# link
echo "existslink" > "${tmps}"/dotfiles/existslink
chmod 700 "${tmps}"/dotfiles/existslink
ln -s "${tmps}"/dotfiles/existslink "${tmpd}"/existslink

# directory
mkdir -p "${tmps}"/dotfiles/direxists
echo "f1-original" > "${tmps}"/dotfiles/direxists/f1
mkdir -p "${tmpd}"/direxists
echo "f1" > "${tmpd}"/direxists/f1
chmod 700 "${tmpd}"/direxists/f1
chmod 700 "${tmpd}"/direxists

# link children
mkdir -p "${tmps}"/dotfiles/linkchildren
echo "f1-original" > "${tmps}"/dotfiles/linkchildren/f1
chmod 700 "${tmps}"/dotfiles/linkchildren/f1
mkdir -p "${tmps}"/dotfiles/linkchildren/d1
chmod 700 "${tmps}"/dotfiles/linkchildren/d1
echo "f2-original" > "${tmps}"/dotfiles/linkchildren/d1/f2
chmod 700 "${tmps}"/dotfiles/linkchildren/d1/f2

mkdir -p "${tmpd}"/linkchildren
chmod 700 "${tmpd}"/linkchildren
echo "f1" > "${tmpd}"/linkchildren/f1
mkdir -p "${tmpd}"/linkchildren/d1
echo "f2" > "${tmpd}"/linkchildren/d1/f2

# no mode
echo 'nomode-original' > "${tmps}"/dotfiles/nomode
echo 'nomode' > "${tmpd}"/nomode

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  force_chmod: true
dotfiles:
  f_f777:
    src: f777
    dst: ${tmpd}/f777
    chmod: preserve
  f_link:
    src: link
    dst: ${tmpd}/link
    chmod: preserve
    link: absolute
  d_dir:
    src: dir
    dst: ${tmpd}/dir
    chmod: preserve
  f_template:
    src: template
    dst: ${tmpd}/template
    chmod: preserve
  f_link_template:
    src: link-template
    dst: ${tmpd}/link-template
    chmod: preserve
  f_exists:
    src: exists
    dst: ${tmpd}/exists
    chmod: preserve
  f_existslink:
    src: existslink
    dst: ${tmpd}/existslink
    chmod: preserve
    link: absolute
  d_direxists:
    src: direxists
    dst: ${tmpd}/direxists
    chmod: preserve
  d_linkchildren:
    src: linkchildren
    dst: ${tmpd}/linkchildren
    chmod: preserve
    link: link_children
  f_nomode:
    src: nomode
    dst: ${tmpd}/nomode
    chmod: preserve
profiles:
  p1:
    dotfiles:
    - f_f777
    - f_link
    - d_dir
    - f_template
    - f_link_template
    - f_exists
    - f_existslink
    - d_direxists
    - d_linkchildren
    - f_nomode
_EOF
#cat ${cfg}

exists_before=$(stat -L -c '%a' "${tmpd}/exists")
direxists_before=$(stat -L -c '%a' "${tmpd}/direxists")
direxists_f1_before=$(stat -L -c '%a' "${tmpd}/direxists/f1")

# install
echo "first round"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V
echo "first round"

# non-existing but will create with "default" rights on preserve
# 644 for file
# 755 for directory
# link will get the rights of the file it points to
has_rights "${tmpd}/f777" "$(get_default_file_mode)"
has_rights "${tmpd}/link" "700"
has_rights "${tmpd}/dir" "$(get_default_dir_mode)"
has_rights "${tmpd}/template" "$(get_default_file_mode)"
# first install to workdir (def rights) and then symlink
has_rights "${tmpd}/link-template" "644"
[ -L "${tmpd}/link-template" ] && echo "link-template is not a symlink" && exit 1

# existing
has_rights "${tmpd}/exists" "700"
has_rights "${tmpd}/exists" "${exists_before}"

has_rights "${tmpd}/existslink" "700" # points back to dotpath
is_same_as "${tmpd}/existslink" "${tmps}/dotfiles/existslink"

has_rights "${tmpd}/direxists" "700"
has_rights "${tmpd}/direxists" "${direxists_before}"

has_rights "${tmpd}/direxists/f1" "700"
has_rights "${tmpd}/direxists/f1" "${direxists_f1_before}"

has_rights "${tmpd}/linkchildren" "700" # default for new directory
has_rights "${tmpd}/linkchildren/f1" "700" # points back to dotpath
has_rights "${tmpd}/linkchildren/d1" "700" # points back to dotpath
has_rights "${tmpd}/linkchildren/d1/f2" "700"

# modify
echo 'f777-2' >> "${tmps}"/dotfiles/f777
chmod 701 "${tmps}"/dotfiles/f777
echo 'link-2' >> "${tmps}"/dotfiles/link
chmod 701 "${tmps}"/dotfiles/link
echo "f1-2" >> "${tmps}"/dotfiles/dir/f1
chmod 701 "${tmps}"/dotfiles/dir
chmod 701 "${tmps}"/dotfiles/dir/f1

f777_before=$(stat -L -c '%a' "${tmpd}/f777")
link_before=$(stat -L -c '%a' "${tmpd}/link")
dir_before=$(stat -L -c '%a' "${tmpd}/dir")

echo "second round"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V
echo "second round"

# existing
has_rights "${tmpd}/f777" "${f777_before}"
has_rights "${tmpd}/link" "${link_before}"
has_rights "${tmpd}/dir" "${dir_before}"

echo "OK"
exit 0
