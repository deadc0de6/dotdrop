#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2025, deadc0de6
#
# test dir_as_block behavior
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

# Setup temp dirs
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
dotpath="${tmpd}/dotfiles"
mkdir -p "${dotpath}"
instroot="${tmpd}/install"
mkdir -p "${instroot}"

clear_on_exit "${tmpd}"

# Create source directories and files
mkdir -p "${dotpath}/blockroot/subdir"
echo "root" > "${dotpath}/blockroot/root.txt"
echo "sub" > "${dotpath}/blockroot/subdir/sub.txt"

mkdir -p "${dotpath}/parent/matchsub"
mkdir -p "${dotpath}/parent/nomatchsub"
echo "match" > "${dotpath}/parent/matchsub/file.txt"
echo "nomatch" > "${dotpath}/parent/nomatchsub/file.txt"

echo "plain" > "${dotpath}/plainfile"

mkdir -p "${dotpath}/linked"
echo "linked" > "${dotpath}/linked/file.txt"

# Create config file
cfg="${tmpd}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: false
  create: true
  dotpath: dotfiles
dotfiles:
  d_blockroot:
    src: blockroot
    dst: ${instroot}/blockroot
    dir_as_block:
      - "*/blockroot"
  d_parent:
    src: parent
    dst: ${instroot}/parent
    dir_as_block:
      - "*/matchsub"
  f_plain:
    src: plainfile
    dst: ${instroot}/plainfile
    dir_as_block:
      - "*plainfile"
  d_linked:
    src: linked
    dst: ${instroot}/linked
    link: absolute
    dir_as_block:
      - "*/linked"
profiles:
  p1:
    dotfiles:
      - d_blockroot
      - d_parent
      - f_plain
      - d_linked
_EOF

# Install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" --verbose -p p1

# Top-level block should replace unmanaged files
echo "extra" > "${instroot}/blockroot/extra.txt"

# Nested matched dir should replace unmanaged files
echo "extra" > "${instroot}/parent/matchsub/extra.txt"

# Nested non-matched dir should keep unmanaged files
echo "extra" > "${instroot}/parent/nomatchsub/extra.txt"

# Reinstall and verify behavior
cd "${ddpath}" | ${bin} install -f -c "${cfg}" --verbose -p p1

[ ! -e "${instroot}/blockroot/extra.txt" ] || \
  (echo "blockroot extra file should be removed" && exit 1)

[ ! -e "${instroot}/parent/matchsub/extra.txt" ] || \
  (echo "matchsub extra file should be removed" && exit 1)

[ -e "${instroot}/parent/nomatchsub/extra.txt" ] || \
  (echo "nomatchsub extra file should be kept" && exit 1)

# Ensure managed files still exist
[ -f "${instroot}/blockroot/root.txt" ] || \
  (echo "blockroot/root.txt missing" && exit 1)
[ -f "${instroot}/parent/matchsub/file.txt" ] || \
  (echo "parent/matchsub/file.txt missing" && exit 1)
[ -f "${instroot}/parent/nomatchsub/file.txt" ] || \
  (echo "parent/nomatchsub/file.txt missing" && exit 1)

# Regular files should not be affected by dir_as_block
echo "changed" > "${instroot}/plainfile"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" --verbose -p p1
grep -q '^plain$' "${instroot}/plainfile" || \
  (echo "plainfile should be installed as a regular file" && exit 1)

# Linked directories should not be handled as blocks
[ -L "${instroot}/linked" ] || \
  (echo "linked should be a symlink" && exit 1)

echo "OK"
exit 0
