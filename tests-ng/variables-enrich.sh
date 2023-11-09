#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6
#
# test variables enrichment
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

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${tmps}/config.yaml"
export dotdrop_test_dst="${tmpd}/def"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
echo "os={{@@ os @@}}" > "${tmps}"/dotfiles/abc
echo "release={{@@ release @@}}" >> "${tmps}"/dotfiles/abc
echo "distro_id={{@@ distro_id @@}}" >> "${tmps}"/dotfiles/abc
echo "distro_like={{@@ distro_like @@}}" >> "${tmps}"/dotfiles/abc
echo "distro_version={{@@ distro_version @@}}" >> "${tmps}"/dotfiles/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 --verbose

pybin="python3"
real_os=$(${pybin} -c 'import platform; print(platform.system().lower())')
real_release=$(${pybin} -c 'import platform; print(platform.release().lower())')
real_distro_id=$(${pybin} -c 'import distro; print(distro.id().lower())')
real_distro_like=$(${pybin} -c 'import distro; print(distro.like().lower())')
real_distro_version=$(${pybin} -c 'import distro; print(distro.version().lower())')

# tests
[ ! -e "${tmpd}"/abc ] && echo "abc not installed" && exit 1
cat "${tmpd}/abc"
  ## only test this on CI/CD
grep "^os=${real_os}" "${tmpd}"/abc >/dev/null
grep "^release=${real_release}" "${tmpd}"/abc >/dev/null
grep "^distro_id=${real_distro_id}" "${tmpd}"/abc >/dev/null
grep "^distro_like=${real_distro_like}" "${tmpd}"/abc >/dev/null
grep "^distro_version=${real_distro_version}" "${tmpd}"/abc >/dev/null

# already defined variables
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
variables:
  os: "abc"
  release: "def"
  distro_id: "ghi"
  distro_like: "jkl"
  distro_version: "mno"
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
rm -f "${tmpd}/abc"

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 --verbose

# tests
[ ! -e "${tmpd}"/abc ] && echo "abc not installed" && exit 1
cat "${tmpd}/abc"
grep '^os=abc$' "${tmpd}"/abc >/dev/null
grep '^release=def$' "${tmpd}"/abc >/dev/null
grep '^distro_id=ghi$' "${tmpd}"/abc >/dev/null
grep '^distro_like=jkl$' "${tmpd}"/abc >/dev/null
grep '^distro_version=mno$' "${tmpd}"/abc >/dev/null

echo "OK"
exit 0
