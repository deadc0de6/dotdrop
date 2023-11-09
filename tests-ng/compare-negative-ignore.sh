#!/usr/bin/env bash
# author: jtt9340 (https://github.com/jtt9340)
# author: deadc0de6
#
# test install negative ignore absolute/relative
# returns 1 in case of error
#

# exit on first error
#set -eu -o errtrace -o pipefail

cur=$(cd "$(dirname "${0}")" && pwd)

# dotdrop path can be pass as argument
ddpath="${cur}/../"
[ -n "${1}" ] && ddpath="${1}"
[ ! -d "${ddpath}" ] && echo "ddpath \"${ddpath}\" is not a directory" && exit 1

PPATH="{PYTHONPATH:-}"
export PYTHONPATH="${ddpath}:${PPATH}"
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
echo "data1" > "${tmpd}"/program/a
echo "data2" > "${tmpd}"/program/ignore_me/b
echo "data3" > "${tmpd}"/program/ignore_me/c

# create the config file
cfg="${basedir}/config.yaml"
create_conf "${cfg}" # sets token

# import
echo "[+] import"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/program

# make some changes to generate a diff
echo "changed1" > "${tmpd}"/program/a
echo "changed1" > "${tmpd}"/program/ignore_me/b
echo "changed1" > "${tmpd}"/program/ignore_me/c

echo "[+] comparing normal - 3 diffs expected"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" --verbose
[ "$?" = 0 ] && exit 1 # We don't want an exit status of 0
cnt=$(cd "${ddpath}" | ${bin} compare -c "${cfg}" | grep '^=> diff' | wc -l)
set -e

[ "${cnt}" != "3" ] && echo "bad number of diff: ${cnt}/3" && exit 1

# expects two diffs
patt0="*/ignore_me/*"
patt1="!*/ignore_me/c"
echo "[+] comparing with ignore (patterns: ${patt0} and ${patt1}) - 2 diffs expected"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" --verbose --ignore="${patt0}" --ignore="${patt1}"
[ "$?" = "0" ] && exit 1
cnt=$(cd "${ddpath}" | ${bin} compare -c "${cfg}" --ignore="${patt0}" --ignore="${patt1}" | grep '^=> diff' | wc -l)
set -e

[ "${cnt}" != "2" ] && echo "bad number of diff: ${cnt}/2" && exit 1


# Adding ignore in dotfile
cfg2="${basedir}/config2.yaml"
# shellcheck disable=SC1004
sed '/d_program:/a\
\ \ \ \ cmpignore:\
\ \ \ \ - "*/ignore_me/*"\
\ \ \ \ - "!*/ignore_me/c"
' "${cfg}" > "${cfg2}"

# still expects two diffs
echo "[+] comparing with ignore in dotfile - 2 diffs expected"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg2}" --verbose
[ "$?" = "0" ] && exit 1
cnt=$(cd "${ddpath}" | ${bin} compare -c "${cfg2}" | grep '^=> diff' | wc -l)
set -e

[ "${cnt}" != "2" ] && echo "bad number of diff: ${cnt}/2" && exit 1

echo "OK"
exit 0
