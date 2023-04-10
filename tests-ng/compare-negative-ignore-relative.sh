#!/usr/bin/env bash
# author: jtt9340 (https://github.com/jtt9340)
#
# test compare negative ignore relative
# returns 1 in case of error
#

## start-cookie
set -e
cur=$(cd "$(dirname "${BASH_SOURCE:-$0}")" && pwd)
ddpath="${cur}/../"
export PYTHONPATH="${ddpath}:${PYTHONPATH}"
altbin="python3 -m dotdrop.dotdrop"
if hash coverage 2>/dev/null; then
  altbin="coverage run -p --source=dotdrop -m dotdrop.dotdrop"
fi
bin="${DT_BIN:-${altbin}}"
# shellcheck source=tests-ng/helpers
source "${cur}"/helpers
echo -e "$(tput setaf 6)==> RUNNING $(basename "${BASH_SOURCE[0]}") <==$(tput sgr0)"
## end-cookie

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

# expects two diffs (no need to test comparing normal - 3 diffs, as that is taken care of in compare-negative-ignore.sh)
patt0="ignore_me/*"
patt1="!ignore_me/c"
echo "[+] comparing with ignore (patterns: ${patt0} and ${patt1}) - 2 diffs"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" --verbose --ignore="${patt0}" --ignore=${patt1}
[ "$?" = "0" ] && exit 1
set -e

########################################
# Test ignores specified in config.yaml
########################################
# add some files
mkdir -p "${tmpd}"/.zsh
echo "some data" > "${tmpd}"/.zsh/somefile
mkdir -p "${tmpd}"/.zsh/plugins
echo "some data" > "${tmpd}"/.zsh/plugins/someplugin

echo "[+] import .zsh"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/.zsh

touch "${tmpd}"/.zsh/plugins/ignore-1.zsh
touch "${tmpd}"/.zsh/plugins/ignore-2.zsh

# adding ignore in config.yaml
cfg2="${basedir}/config2.yaml"
sed '/d_zsh:/a\
\ \ \ \ cmpignore:\
\ \ \ \ - "plugins/ignore-?.zsh"\
\ \ \ \ - "!plugins/ignore-2.zsh"
' "${cfg}" > "${cfg2}"

# expects one diff
patt0="plugins/ignore-?.zsh"
patt1="!plugins/ignore-2.zsh"
echo "[+] comparing with ignore (patterns: ${patt0} and ${patt1}) - 1 diff"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg}" --verbose -C "${tmpd}"/.zsh --ignore="${patt0}" --ignore=${patt1}
[ "$?" = "0" ] && exit 1
set -e

# expects one diff
echo "[+] comparing .zsh with ignore in dotfile - 1 diff expected"
set +e
cd "${ddpath}" | ${bin} compare -c "${cfg2}" --verbose -C "${tmpd}"/.zsh
ret="$?"
echo ${ret}
[ "${ret}" = "0" ] && exit 1
set -e

echo "OK"
