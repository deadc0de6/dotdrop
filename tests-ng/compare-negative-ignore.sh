#!/usr/bin/env bash
# author: jtt9340 (https://github.com/jtt9340)
#
# test install negative ignore absolute/relative
# returns 1 in case of error
#

# exit on first error
#set -e

cur=$(cd "$(dirname "${0}")" && pwd)

# dotdrop path can be pass as argument
ddpath="${cur}/../"
[ -n "${1}" ] && ddpath="${1}"
[ ! -d "${ddpath}" ] && echo "ddpath \"${ddpath}\" is not a directory" && exit 1

export PYTHONPATH="${ddpath}:${PYTHONPATH}"
bin="python3 -m dotdrop.dotdrop"

echo "dotdrop path: ${ddpath}"
echo "pythonpath: ${PYTHONPATH}"

# get the helpers
# shellcheck source=tests-ng/helpers
source "${cur}"/helpers

echo -e "$(tput setaf 6)==> RUNNING $(basename "${BASH_SOURCE[0]}") <==$(tput sgr0)"

################################################################
# this is the test
################################################################

# dotdrop directory
basedir=$(mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d)
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"

# the dotfile to be imported
tmpd=$(mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d)

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

# some files
mkdir -p "${tmpd}"/program/ignore_me
echo "some data" > "${tmpd}"/program/a
echo "some data" > "${tmpd}"/program/ignore_me/b
echo "some data" > "${tmpd}"/program/ignore_me/c

# create the config file
cfg="${basedir}/config.yaml"
create_conf "${cfg}" # sets token

# import
echo "[+] import"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/program

# make some changes to generate a diff
echo "some other data" > "${tmpd}"/program/a
echo "some other data" > "${tmpd}"/program/ignore_me/b
echo "some other data" > "${tmpd}"/program/ignore_me/c

echo "[+] comparing normal - 3 diffs"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" --verbose
[ "$?" = 0 ] && exit 1 # We don't want an exit status of 0
set -e

# expects two diffs
patt0="*/ignore_me/*"
patt1="!*/ignore_me/c"
echo "[+] comparing with ignore (patterns: ${patt0} and ${patt1}) - 2 diffs"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" --verbose --ignore="${patt0}" --ignore="${patt1}"
[ "$?" = "0" ] && exit 1
set -e

# Adding ignore in dotfile
cfg2="${basedir}/config2.yaml"
# shellcheck disable=SC1004
sed '/d_program:/a\
\ \ \ \ cmpignore:\
\ \ \ \ - "*/ignore_me/*"\
\ \ \ \ - "!*/ignore_me/c"
' "${cfg}" > "${cfg2}"

# still expects two diffs
echo "[+] comparing with ignore in dotfile - 2 diffs"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg2}" --verbose
[ "$?" = "0" ] && exit 1
set -e

echo "OK"
exit 0
