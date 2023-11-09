#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test import not existing
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

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the dotfile
echo "test" > "${tmps}"/dotfiles/abc

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_variables:
  - /variables/does/not/exist:optional
  - /variables/does/not/::exist:optional
  - /variables/*/not/exist:optional
  import_actions:
  - /actions/does/not/exist:optional
  - /actions/does/not/::exist:optional
  - /actions/does/*/exist:optional
  import_configs:
  - /configs/does/not/exist:optional
  - /configs/does/not/::exist:optional
  - /configs/does/not/*:optional
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

# dummy call
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -V

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_variables:
  - /variables/does/not/exist
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# dummy call
set +e
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -V
[ "$?" = "0" ] && echo "variables" && exit 1
set -e

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_variables:
  - /variables/does/not/exist:with/separator
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# dummy call
set +e
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -V
[ "$?" = "0" ] && echo "variables with separator" && exit 1
set -e

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_variables:
  - /variables/*/not/exist
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# dummy call
set +e
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -V
[ "$?" = "0" ] && echo "variables glob" && exit 1
set -e

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_actions:
  - /actions/does/not/exist
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# dummy call
set +e
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -V
[ "$?" = "0" ] && echo "actions" && exit 1
set -e

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_actions:
  - /actions/does/not:exist/with/separator
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# dummy call
set +e
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -V
[ "$?" = "0" ] && echo "actions with separator" && exit 1
set -e

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_actions:
  - /actions/does/*/exist
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# dummy call
set +e
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -V
[ "$?" = "0" ] && echo "actions glob" && exit 1
set -e

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_configs:
  - /configs/does/not/exist
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# dummy call
set +e
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -V
[ "$?" = "0" ] && echo "configs" && exit 1
set -e

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_configs:
  - /configs/does:not/exist/with/separator
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# dummy call
set +e
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -V
[ "$?" = "0" ] && echo "configs with separator" && exit 1
set -e

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  import_configs:
  - /configs/does/not/*
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# dummy call
set +e
cd "${ddpath}" | ${bin} files -c "${cfg}" -p p1 -V
[ "$?" = "0" ] && echo "configs glob" && exit 1
set -e

echo "OK"
exit 0
