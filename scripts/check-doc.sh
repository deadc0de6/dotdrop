#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6

# stop on first error
set -eu -o errtrace -o pipefail

## test doc external links
echo "------------------------"
echo "checking external links"
find . -type f -iname '*.md' | while read -r line; do
  ./scripts/check_links.py "${line}"
done

## test the doc internal links
## https://github.com/remarkjs/remark-validate-links
## https://github.com/tcort/markdown-link-check
## npm install -g remark-cli remark-validate-links
if ! which remark >/dev/null 2>&1; then
  echo "[WARNING] install \"remark\" to test the doc"
  exit 1
fi

in_cicd="${GH_WORKFLOW:-}"
if [ -n "${in_cicd}" ]; then
  echo "------------------------"
  echo "checking internal links"
  find . -type f -iname '*.md' | while read -r line; do
    remark -f -u validate-links "${line}"
  done
else
  echo "not checking internal links..."
fi

echo "documentation OK"
