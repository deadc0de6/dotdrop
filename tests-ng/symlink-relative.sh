#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6
#
# test relative symlink
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
tmpw=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
export DOTDROP_WORKDIR="${tmpw}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpw}"

##################################################
# test symlink directory
##################################################
# create the file
echo "file1" > "${tmps}"/dotfiles/abc
mkdir -p "${tmps}"/dotfiles/def
echo 'file2' > "${tmps}"/dotfiles/def/afile
echo '{{@@ header() @@}}' > "${tmps}"/dotfiles/ghi
mkdir -p "${tmps}"/dotfiles/jkl
echo '{{@@ header() @@}}' > "${tmps}"/dotfiles/jkl/anotherfile

# create the config file
cfg="${tmps}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_dotfile_default: nolink
  workdir: ${tmpw}
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    link: relative
  f_abc2:
    dst: ${tmpd}/abc2
    src: abc
    link: absolute
  d_def:
    dst: ${tmpd}/def
    src: def
    link: relative
  f_ghi:
    dst: ${tmpd}/ghi
    src: ghi
    link: relative
  d_jkl:
    dst: ${tmpd}/jkl
    src: jkl
    link: relative
profiles:
  p1:
    dotfiles:
    - f_abc
    - f_abc2
    - d_def
    - f_ghi
    - d_jkl
_EOF
#cat ${cfg}

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

# ensure exists and is link
[ ! -h "${tmpd}"/abc ] && echo "not a symlink" && exit 1
[ ! -h "${tmpd}"/abc2 ] && echo "not a symlink" && exit 1
[ ! -h "${tmpd}"/def ] && echo "not a symlink" && exit 1
[ ! -d "${tmpd}"/def ] && echo "not a symlink" && exit 1
[ ! -h "${tmpd}"/ghi ] && echo "not a symlink" && exit 1
[ ! -h "${tmpd}"/jkl ] && echo "not a symlink" && exit 1
[ ! -d "${tmpd}"/jkl ] && echo "not a symlink" && exit 1

# shellcheck disable=SC2010
ls -l "${tmpd}"/abc | grep '\.\.' || exit 1
ls -l "${tmpd}"/abc2
# shellcheck disable=SC2010
ls -l "${tmpd}"/def | grep '\.\.' || exit 1
# shellcheck disable=SC2010
ls -l "${tmpd}"/ghi | grep '\.\.' || exit 1
# shellcheck disable=SC2010
ls -l "${tmpd}"/jkl | grep '\.\.' || exit 1

grep 'file1' "${tmpd}"/abc
grep 'file1' "${tmpd}"/abc2
grep 'file2' "${tmpd}"/def/afile
grep 'This dotfile is managed using dotdrop' "${tmpd}"/ghi
grep 'This dotfile is managed using dotdrop' "${tmpd}"/jkl/anotherfile

[[ $(realpath --relative-base="${tmpw}" -- "$(realpath "${tmpd}"/ghi)") =~ "^/" ]] && echo "ghi not subpath of workdir" && exit 1
[[ $(realpath --relative-base="${tmpw}" -- "$(realpath "${tmpd}"/jkl)") =~ ^/ ]] && echo "jkl not subpath of workdir" && exit 1


#############################################################################################################################

rm -rf "${tmps}" "${tmpd}" "${tmpw}"

# the dotfile source
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
tmpd="${tmps}"
mkdir -p "${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the file
echo "file1" > "${tmps}"/dotfiles/abc
mkdir -p "${tmps}"/dotfiles/def
echo 'file2' > "${tmps}"/dotfiles/def/afile

# create the config file
cfg="${tmps}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_dotfile_default: nolink
  workdir: ${tmpw}
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
    link: relative
  f_abc2:
    dst: ${tmpd}/abc2
    src: abc
    link: absolute
  d_def:
    dst: ${tmpd}/def
    src: def
    link: relative
profiles:
  p1:
    dotfiles:
    - f_abc
    - f_abc2
    - d_def
_EOF
#cat ${cfg}

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

# ensure exists and is link
[ ! -h "${tmpd}"/abc ] && echo "not a symlink" && exit 1
[ ! -h "${tmpd}"/abc2 ] && echo "not a symlink" && exit 1
[ ! -h "${tmpd}"/def ] && echo "not a symlink" && exit 1
[ ! -d "${tmpd}"/def ] && echo "not a symlink" && exit 1

grep 'file1' "${tmpd}"/abc
grep 'file1' "${tmpd}"/abc2
grep 'file2' "${tmpd}"/def/afile

echo "OK"
exit 0
