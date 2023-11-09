#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test the use of the keyword "import" in profiles
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
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
extdotfiles="${tmps}/df_p1.yaml"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

dynextdotfiles_name="d_uid_dynvar"
dynextdotfiles="${tmps}/ext_${dynextdotfiles_name}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dynvariables:
  d_uid: "echo ${dynextdotfiles_name}"
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
  f_def:
    dst: ${tmpd}/def
    src: def
  f_xyz:
    dst: ${tmpd}/xyz
    src: xyz
  f_dyn:
    dst: ${tmpd}/dyn
    src: dyn
profiles:
  p1:
    dotfiles:
    - f_abc
    import:
    - $(basename "${extdotfiles}")
    - "ext_{{@@ d_uid @@}}"
_EOF

# create the external dotfile file
cat > "${extdotfiles}" << _EOF
dotfiles:
  - f_def
  - f_xyz
_EOF

cat > "${dynextdotfiles}" << _EOF
dotfiles:
  - f_dyn
_EOF

# create the source
mkdir -p "${tmps}"/dotfiles/
echo "abc" > "${tmps}"/dotfiles/abc
echo "def" > "${tmps}"/dotfiles/def
echo "xyz" > "${tmps}"/dotfiles/xyz
echo "dyn" > "${tmps}"/dotfiles/dyn

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

# checks
[ ! -e "${tmpd}"/abc ] && exit 1
[ ! -e "${tmpd}"/def ] && exit 1
[ ! -e "${tmpd}"/xyz ] && exit 1
[ ! -e "${tmpd}"/dyn ] && exit 1
echo 'file found'
grep 'abc' "${tmpd}"/abc >/dev/null 2>&1
grep 'def' "${tmpd}"/def >/dev/null 2>&1
grep 'xyz' "${tmpd}"/xyz >/dev/null 2>&1
grep 'dyn' "${tmpd}"/dyn >/dev/null 2>&1

echo "OK"
exit 0
