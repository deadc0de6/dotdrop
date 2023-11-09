#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test install ignore absolute/relative
# returns 1 in case of error
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

# dotdrop directory
basedir=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
echo "[+] dotdrop dir: ${basedir}"
echo "[+] dotpath dir: ${basedir}/dotfiles"

# the dotfile to be imported
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
tmps="${basedir}"

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

# some files
mkdir -p "${tmpd}"/{program,config,vscode}
echo "some data" > "${tmpd}"/program/a
echo "some data" > "${tmpd}"/config/a
echo "some data" > "${tmpd}"/vscode/extensions.txt
echo "some data" > "${tmpd}"/vscode/keybindings.json

# create the config file
cfg="${basedir}/config.yaml"
create_conf "${cfg}" # sets token

# import
echo "[+] import"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/program
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/config
cd "${ddpath}" | ${bin} import -f -c "${cfg}" "${tmpd}"/vscode

# add files on filesystem
echo "[+] add files"
echo "new data" > "${basedir}"/dotfiles/"${tmpd}"/README.md
echo "new data" > "${basedir}"/dotfiles/"${tmpd}"/vscode/README.md
echo "new data" > "${basedir}"/dotfiles/"${tmpd}"/program/README.md
mkdir -p "${basedir}"/dotfiles/"${tmpd}"/readmes
echo "new data" > "${basedir}"/dotfiles/"${tmpd}"/readmes/README.md

# install
rm -rf "${tmpd}"
echo "[+] install normal"
cd "${ddpath}" | ${bin} install --showdiff -c "${cfg}" --verbose -f
[ "$?" != "0" ] && exit 1
nb=$(find "${tmpd}" -iname 'README.md' | wc -l)
echo "(1) found ${nb} README.md file(s)"
[ "${nb}" != "2" ] && exit 1

# adding ignore in dotfile
cfg2="${basedir}/config2.yaml"
sed '/d_program:/a \ \ \ \ instignore:\n\ \ \ \ - "README.md"' "${cfg}" > "${cfg2}"
cat "${cfg2}"

# install
rm -rf "${tmpd}"
echo "[+] install with ignore in dotfile"
cd "${ddpath}" | ${bin} install -c "${cfg2}" --verbose -f
[ "$?" != "0" ] && exit 1
nb=$(find "${tmpd}" -iname 'README.md' | wc -l)
echo "(2) found ${nb} README.md file(s)"
[ "${nb}" != "1" ] && exit 1

# adding ignore in config
cfg2="${basedir}/config2.yaml"
sed '/^config:/a \ \ instignore:\n\ \ - "README.md"' "${cfg}" > "${cfg2}"
cat "${cfg2}"

# install
rm -rf "${tmpd}"
echo "[+] install with ignore in config"
cd "${ddpath}" | ${bin} install -c "${cfg2}" --verbose -f
[ "$?" != "0" ] && exit 1
nb=$(find "${tmpd}" -iname 'README.md' | wc -l)
echo "(3) found ${nb} README.md file(s)"
[ "${nb}" != "0" ] && exit 1

## reinstall to trigger showdiff
echo "showdiff" > "${tmpd}"/program/a
(
  cd "${ddpath}"
  printf "y\n" | ${bin} install --showdiff -c "${cfg}" --verbose -f
  exit $?
)

# test templated subdir
cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF

mkdir -p "${tmpd}"/nvim
mkdir -p "${tmpd}"/nvim/dir1
echo "f1" > "${tmpd}"/nvim/dir1/file1
mkdir -p "${tmpd}"/nvim/dir2
echo "f1" > "${tmpd}"/nvim/dir2/file2
echo "ftop" > "${tmpd}"/nvim/ftop

echo "[+] import top"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -l link_children -p p1 "${tmpd}"/nvim

# add sub dir
mkdir -p "${tmpd}"/nvim/templated
echo "noprofile" > "${tmpd}"/nvim/templated/ftemplated
echo "noprofile" > "${tmpd}"/nvim/template

echo "[+] import sub"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 "${tmpd}"/nvim/templated
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 "${tmpd}"/nvim/template

cfg2="${basedir}/config2.yaml"
sed '/d_nvim:/a \ \ \ \ instignore:\n\ \ \ \ - "*template*"' "${cfg}" > "${cfg2}"
cat "${cfg2}"

## clean destination files
rm -rf "${tmpd}"/nvim
## patch template file
echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/"${tmpd}"/nvim/templated/ftemplated
echo "{{@@ profile @@}}" > "${tmps}"/dotfiles/"${tmpd}"/nvim/template

echo "[+] install link_children"
cd "${ddpath}" | ${bin} install -f -c "${cfg2}" -p p1 -V d_nvim

[ -d "${tmpd}"/nvim/templated ] && echo "templated should not be installed" && exit 1
[ -e "${tmpd}"/nvim/templated/ftemplated ] && echo "templated file should not be installed" && exit 1
[ -e "${tmpd}"/nvim/template ] && echo "template file should not be installed" && exit 1

echo "[+] install sub"
cd "${ddpath}" | ${bin} install -f -c "${cfg2}" -p p1 -V d_templated
echo "[+] install template"
cd "${ddpath}" | ${bin} install -f -c "${cfg2}" -p p1 -V f_template

[ ! -d "${tmpd}"/nvim/templated ] && echo "templated not installed" && exit 1
[ ! -e "${tmpd}"/nvim/templated/ftemplated ] && echo "templated file not installed" && exit 1
[ ! -e "${tmpd}"/nvim/template ] && echo "template file not installed" && exit 1
grep 'p1' "${tmpd}"/nvim/templated/ftemplated
grep 'p1' "${tmpd}"/nvim/template

echo "OK"
exit 0
