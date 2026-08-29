#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test update of templates inside imported directories
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
# the workdir
tmpw=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
export DOTDROP_WORKDIR="${tmpw}"
echo "workdir: ${tmpw}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpw}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  workdir: ${tmpw}
dotfiles:
  d_dir:
    dst: ${tmpd}/dir
    src: dir
profiles:
  p1:
    dotfiles:
    - d_dir
_EOF

# create the dotfile directory with a templated subfile
mkdir -p "${tmps}"/dotfiles/dir/sub
cat > "${tmps}"/dotfiles/dir/sub/file << _EOF
head
{%@@ if profile == "p1" @@%}
is p1
{%@@ else @@%}
is not p1
{%@@ endif @@%}
tail
_EOF

# install
${bin} install -p p1 --cfg "${cfg}"

# the installed subfile should be resolved
inst="${tmpd}/dir/sub/file"
grep 'is p1' "${inst}" >/dev/null 2>&1
grep -v 'is not p1' "${inst}" >/dev/null 2>&1

# save the dotpath subfile content for later comparison
dotfile="${tmps}/dotfiles/dir/sub/file"
cp "${dotfile}" "${tmps}/dotfile.orig"

# modify the installed subfile
cat > "${inst}" << _EOF
head
is p1
modified tail
_EOF

# update should NOT touch the dotpath subfile since it's a template
set +e
out=$(${bin} update -P -p p1 -k d_dir --cfg "${cfg}" 2>&1)
set -e

# the warning should be emitted
echo "${out}" | grep 'uses template, update manually' >/dev/null 2>&1

# the dotpath subfile should be unchanged
if ! diff -q "${dotfile}" "${tmps}/dotfile.orig" >/dev/null 2>&1; then
  echo "dotpath subfile was modified by update!"
  exit 1
fi

echo "OK"
exit 0