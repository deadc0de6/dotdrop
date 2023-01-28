#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6

## test doc external links
find . -type f -iname '*.md' | while read -r line; do
  ./scripts/check_links.py "${line}"
done

## test the doc internal links
## https://github.com/remarkjs/remark-validate-links
## https://github.com/tcort/markdown-link-check
## npm install -g remark-cli remark-validate-links
set +e
which remark >/dev/null 2>&1
r="$?"
set -e
if [ "$r" != "0" ]; then
  echo "[WARNING] install \"remark\" to test the doc"
  exit 1
fi

find . -type f -iname '*.md' | while read -r line; do
  remark -f -u validate-links "${line}"
done

echo "documentation OK"
