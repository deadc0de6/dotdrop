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
[ -f "${instroot}/blockme1/file1.txt" ] || (echo "blockme1 not restored" && exit 1)

# Remove a file from noblock, reinstall, and check it is restored
rm -f "${instroot}/noblock/file4.txt"
cd "${ddpath}" | ${bin} install -f -c "${cfg}" --verbose -p p1
[ -f "${instroot}/noblock/file4.txt" ] || (echo "noblock not restored" && exit 1)

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

# Check confirmation prompts for block and non-block directories
# Remove -f to enable confirmation prompts

# Function to count confirmation prompts in output
count_prompts() {
  grep -c "Do you want to continue" "$1"
}

# Test: blockme1 (should prompt ONCE for the whole dir)
rm -rf "${instroot}/blockme1"
# Use script to simulate 'y' input and capture output
script -q -c "cd \"${ddpath}\" && ${bin} install -c \"${cfg}\" --verbose -p p1" blockme1.out <<<'y'
blockme1_prompts=$(count_prompts blockme1.out)
if [ "$blockme1_prompts" -ne 1 ]; then
  echo "blockme1: expected 1 prompt, got $blockme1_prompts" && exit 1
fi

# Test: noblock (should prompt for each file)
rm -rf "${instroot}/noblock"
script -q -c "cd \"${ddpath}\" && ${bin} install -c \"${cfg}\" --verbose -p p1" noblock.out <<<'y
y'
noblock_prompts=$(count_prompts noblock.out)
# There is only one file, so expect 1 prompt
if [ "$noblock_prompts" -ne 1 ]; then
  echo "noblock: expected 1 prompt, got $noblock_prompts" && exit 1
fi

# Test: blockme1 with multiple files (should still prompt ONCE)
rm -rf "${instroot}/blockme1"
# Add another file to blockme1
echo "fileX" > "${dotpath}/blockme1/fileX.txt"
script -q -c "cd \"${ddpath}\" && ${bin} install -c \"${cfg}\" --verbose -p p1" blockme1_multi.out <<<'y'
blockme1_multi_prompts=$(count_prompts blockme1_multi.out)
if [ "$blockme1_multi_prompts" -ne 1 ]; then
  echo "blockme1 (multi): expected 1 prompt, got $blockme1_multi_prompts" && exit 1
fi

# Test: blockme1/nomatchsub (should prompt for each file in non-block subdir)
rm -rf "${instroot}/blockme1/nomatchsub"
script -q -c "cd \"${ddpath}\" && ${bin} install -c \"${cfg}\" --verbose -p p1" nomatchsub.out <<<'y'
nomatchsub_prompts=$(count_prompts nomatchsub.out)
# Only one file, so expect 1 prompt
if [ "$nomatchsub_prompts" -ne 1 ]; then
  echo "nomatchsub: expected 1 prompt, got $nomatchsub_prompts" && exit 1
fi

# Test: blockme1/matchsub (should prompt ONCE for the whole subdir)
rm -rf "${instroot}/blockme1/matchsub"
script -q -c "cd \"${ddpath}\" && ${bin} install -c \"${cfg}\" --verbose -p p1" matchsub.out <<<'y'
matchsub_prompts=$(count_prompts matchsub.out)
if [ "$matchsub_prompts" -ne 1 ]; then
  echo "matchsub: expected 1 prompt, got $matchsub_prompts" && exit 1
fi

# Check confirmation prompt count for block directory
rm -f "${instroot}/blockme1/file1.txt"
# Run install interactively and capture output
prompt_output_block=$(cd "${ddpath}" && echo y | ${bin} install -c "${cfg}" --verbose -p p1 2>&1)
# Count confirmation prompts (look for 'Overwrite' or 'replace' or similar)
prompt_count_block=$(echo "$prompt_output_block" | grep -E -i 'overwrite|replace|confirm' | wc -l)
if [ "$prompt_count_block" -ne 1 ]; then
  echo "Expected 1 confirmation prompt for block directory, got $prompt_count_block" && exit 1
fi

# Check confirmation prompt count for non-block directory
rm -f "${instroot}/noblock/file4.txt"
# Run install interactively and capture output
prompt_output_noblock=$(cd "${ddpath}" && echo y | ${bin} install -c "${cfg}" --verbose -p p1 2>&1)
# Count confirmation prompts (should be at least 1 for the file, could be more if more files)
prompt_count_noblock=$(echo "$prompt_output_noblock" | grep -E -i 'overwrite|replace|confirm' | wc -l)
if [ "$prompt_count_noblock" -lt 1 ]; then
  echo "Expected at least 1 confirmation prompt for non-block directory, got $prompt_count_noblock" && exit 1
fi

echo "OK"
exit 0
