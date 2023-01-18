#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2022, deadc0de6

## test the doc with linkcheckMarkdown
## pip install --user linkcheckmd
set +e
which linkcheckMarkdown >/dev/null 2>&1
r="$?"
set -e
if [ "$r" != "0" ]; then
  echo "[ERROR] install \"linkcheckMarkdown\" to test for dead links"
  exit 1
fi
find . -type f -iname '*.md' | while read line; do
  echo "checking links in \"${line}\""
  linkcheckMarkdown ${line}
done


### test the doc with remark
### https://github.com/remarkjs/remark-validate-links
#set +e
#which remark >/dev/null 2>&1
#r="$?"
#set -e
#if [ "$r" != "0" ]; then
#  echo "[WARNING] install \"remark\" to test the doc"
#else
#  remark -f -u validate-links docs/
#  remark -f -u validate-links *.md
#fi

### test the doc with markdown-link-check
### https://github.com/tcort/markdown-link-check
#set +e
#which markdown-link-check >/dev/null 2>&1
#r="$?"
#set -e
#if [ "$r" != "0" ]; then
#  echo "[WARNING] install \"markdown-link-check\" to test the doc"
#else
#  for i in `find docs -iname '*.md'`; do markdown-link-check $i; done
#  markdown-link-check README.md
#fi

echo "documentation OK"