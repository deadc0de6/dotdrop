#!/bin/sh
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6

# stop on first error
set -ev

# PEP8 tests
which pycodestyle >/dev/null 2>&1
[ "$?" != "0" ] && echo "Install pycodestyle" && exit 1
echo "testing with pycodestyle"
pycodestyle --ignore=W503,W504,W605 dotdrop/
pycodestyle tests/
pycodestyle scripts/

# pyflakes tests
echo "testing with pyflakes"
pyflakes dotdrop/
pyflakes tests/

# retrieve the nosetests binary
nosebin="nosetests"
which ${nosebin} >/dev/null 2>&1
[ "$?" != "0" ] && nosebin="nosetests3"
which ${nosebin} >/dev/null 2>&1
[ "$?" != "0" ] && echo "Install nosetests" && exit 1

# do not print debugs when running tests (faster)
export DOTDROP_FORCE_NODEBUG=yes

# coverage file location
cur=`dirname $(readlink -f "${0}")`
export COVERAGE_FILE="${cur}/.coverage"

# execute tests with coverage
if [ -z ${GITHUB_WORKFLOW} ]; then
  PYTHONPATH="dotdrop" ${nosebin} --processes=0 --with-coverage --cover-package=dotdrop
  #PYTHONPATH="dotdrop" ${nosebin} -s --processes=-1 --with-coverage --cover-package=dotdrop
else
  PYTHONPATH="dotdrop" ${nosebin} --processes=-1 --with-coverage --cover-package=dotdrop
  #PYTHONPATH="dotdrop" ${nosebin} --processes=0 --with-coverage --cover-package=dotdrop
fi
#PYTHONPATH="dotdrop" python3 -m pytest tests

# enable debug logs
export DOTDROP_DEBUG=yes
unset DOTDROP_FORCE_NODEBUG
# do not print debugs when running tests (faster)
#export DOTDROP_FORCE_NODEBUG=yes

## execute bash script tests
[ "$1" = '--python-only' ] || {
  echo "doing extended tests"
  logdir=`mktemp -d`
  for scr in tests-ng/*.sh; do
    logfile="${logdir}/`basename ${scr}`.log"
    echo "-> running test ${scr} (logfile:${logfile})"
    set +e
    ${scr} > "${logfile}" 2>&1
    if [ "$?" -ne 0 ]; then
      cat ${logfile}
      echo "test ${scr} finished with error"
      rm -rf ${logdir}
      exit 1
    elif grep Traceback ${logfile}; then
      cat ${logfile}
      echo "test ${scr} crashed"
      rm -rf ${logdir}
      exit 1
    fi
    set -e
    echo "test ${scr} ok"
  done
  rm -rf ${logdir}
}

## test the doc with remark
## https://github.com/remarkjs/remark-validate-links
set +e
which remark >/dev/null 2>&1
r="$?"
set -e
if [ "$r" != "0" ]; then
  echo "[WARNING] install \"remark\" to test the doc"
else
  remark -f -u validate-links docs/
  remark -f -u validate-links *.md
fi

## test the doc with markdown-link-check
## https://github.com/tcort/markdown-link-check
set +e
which markdown-link-check >/dev/null 2>&1
r="$?"
set -e
if [ "$r" != "0" ]; then
  echo "[WARNING] install \"markdown-link-check\" to test the doc"
else
  for i in `find docs -iname '*.md'`; do markdown-link-check $i; done
  markdown-link-check README.md
fi

## done
echo "All test finished successfully in ${SECONDS}s"
