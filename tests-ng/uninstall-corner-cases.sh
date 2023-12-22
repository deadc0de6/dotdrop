#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6
#
# test uninstall (no symlink)
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
tmps_dotpath="${tmps}/dotfiles"
mkdir -p "${tmps_dotpath}"
echo "dotfiles source (dotpath): ${tmps}"
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
echo "dotfiles destination: ${tmpd}"
tmpw=$(mktemp -d --suffix='-dotdrop-workdir' || mktemp -d)
echo "workdir: ${tmpw}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpw}"

# config file
# create the config file
link_type="nolink"
file_link="${link_type}"
dir_link="${file_link}"
cfg="${tmps}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_dotfile_default: ${link_type}
  workdir: ${tmpw}
dotfiles:
  f_x:
    src: x
    dst: ${tmpd}/x
    link: ${file_link}
  d_y:
    src: y
    dst: ${tmpd}/y
    link: ${dir_link}
  f_t:
    src: t
    dst: ${tmpd}/t
    link: ${file_link}
  d_z:
    src: z
    dst: ${tmpd}/z
    link: ${dir_link}
  f_trans:
    src: trans
    dst: ${tmpd}/trans
    link: ${file_link}
profiles:
  p1:
    dotfiles:
    - f_x
    - d_y
    - f_t
    - d_z
    - f_trans
_EOF

# create files in dotpath
echo "create contents in dotpath"
content="content-in-dotpath"
pro_templ="{{@@ profile @@}}"

echo "${content}" > "${tmps_dotpath}"/x
mkdir -p "${tmps_dotpath}"/y
echo "${content}" > "${tmps_dotpath}"/y/file
mkdir -p "${tmps_dotpath}"/y/subdir
echo "${content}" > "${tmps_dotpath}"/y/subdir/subfile
echo "profile: ${pro_templ}" > "${tmps_dotpath}"/t
mkdir -p "${tmps_dotpath}"/z
echo "profile t1: ${pro_templ}" > "${tmps_dotpath}"/z/t1
echo "profile t2: ${pro_templ}" > "${tmps_dotpath}"/z/t2
echo "${content}" > "${tmps_dotpath}"/z/file
echo "trans:${pro_templ}" > "${tmps_dotpath}"/trans

# create files to have backup kicks in
content="content-in-fs"
echo "${content}" > "${tmpd}"/x

# install
cd "${ddpath}" && ${bin} install -c "${cfg}" -f -p p1 | grep '^5 dotfile(s) installed.$'

# uninstall dry
cd "${ddpath}" && ${bin} uninstall --dry -c "${cfg}" -f -p p1

echo "OK"
exit 0