#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2025, deadc0de6
#
# test dir_as block
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
mkdir -p "${dotpath}/blockme1/subdir"
echo "file1" > "${dotpath}/blockme1/file1.txt"
echo "file2" > "${dotpath}/blockme1/subdir/file2.txt"

mkdir -p "${dotpath}/blockme2"
echo "file3" > "${dotpath}/blockme2/file3.txt"

mkdir -p "${dotpath}/noblock"
echo "file4" > "${dotpath}/noblock/file4.txt"

# Add a subdirectory that matches the dir_as_block pattern
mkdir -p "${dotpath}/blockme1/matchsub"
echo "subfile1" > "${dotpath}/blockme1/matchsub/subfile1.txt"

# Add a subdirectory that does NOT match the pattern
mkdir -p "${dotpath}/blockme1/nomatchsub"
echo "subfile2" > "${dotpath}/blockme1/nomatchsub/subfile2.txt"

# Create config file with multiple dir_as_block patterns
cfg="${tmpd}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: false
  create: true
  dotpath: dotfiles
dotfiles:
  d_blockme1:
    src: blockme1
    dst: ${instroot}/blockme1
    dir_as_block:
      - "*blockme1"
      - "*blockme2"
  d_blockme2:
    src: blockme2
    dst: ${instroot}/blockme2
    dir_as_block:
      - "*blockme1"
      - "*blockme2"
  d_noblock:
    src: noblock
    dst: ${instroot}/noblock
    dir_as_block:
      - "*blockme1"
      - "*blockme2"
profiles:
  p1:
    dotfiles:
      - d_blockme1
      - d_blockme2
      - d_noblock
_EOF

# Install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" --verbose -p p1

# Check that blockme1 and blockme2 were installed as a block (directory replaced as a whole)
# Remove a file from blockme1, reinstall, and check it is restored (block behavior)
rm -f "${instroot}/blockme1/file1.txt"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" --verbose -p p1
[ -f "${instroot}/blockme1/file1.txt" ] || (echo "blockme1 not restored as block" && exit 1)

# Remove a file from noblock, reinstall, and check it is NOT restored (not a block)
rm -f "${instroot}/noblock/file4.txt"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" --verbose -p p1
[ ! -f "${instroot}/noblock/file4.txt" ] || (echo "noblock should not be restored as block" && exit 1)

# Check that blockme2 was installed as a block
rm -f "${instroot}/blockme2/file3.txt"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" --verbose -p p1
[ -f "${instroot}/blockme2/file3.txt" ] || (echo "blockme2 not restored as block" && exit 1)

# Check that subdir and its file are present in blockme1
[ -d "${instroot}/blockme1/subdir" ] || (echo "blockme1/subdir missing" && exit 1)
[ -f "${instroot}/blockme1/subdir/file2.txt" ] || (echo "blockme1/subdir/file2.txt missing" && exit 1)

# Reinstall to ensure both subdirs are installed
cd "${ddpath}" | ${bin} install -f -c "${cfg}" --verbose -p p1

# Remove a file from the matching subdir, reinstall, and check it is restored (block behavior)
rm -f "${instroot}/blockme1/matchsub/subfile1.txt"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" --verbose -p p1
[ -f "${instroot}/blockme1/matchsub/subfile1.txt" ] || (echo "blockme1/matchsub not restored as block" && exit 1)

# Remove a file from the non-matching subdir, reinstall, and check it is NOT restored (not a block)
rm -f "${instroot}/blockme1/nomatchsub/subfile2.txt"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" --verbose -p p1
[ ! -f "${instroot}/blockme1/nomatchsub/subfile2.txt" ] || (echo "blockme1/nomatchsub should not be restored as block" && exit 1)

echo "OK"
exit 0
