#!/usr/bin/env bash
# author: jtt9340 (https://github.com/jtt9340)
#
# test global negative ignore update
# returns 1 in case of error
#

# exit on first error
set -e

# all this crap to get current path
rl="readlink -f"
if ! ${rl} "${0}" >/dev/null 2>&1; then
  rl="realpath"

  if ! hash ${rl}; then
    echo "\"${rl}\" not found !" && exit 1
  fi
fi
cur=$(dirname "$(${rl} "${0}")")

# dotdrop path can be pass as argument
ddpath="${cur}/../"
[ -n "${1}" ] && ddpath="${1}"
[ ! -d "${ddpath}" ] && echo "ddpath \"${ddpath}\" is not a directory" && exit 1

export PYTHONPATH="${ddpath}:${PYTHONPATH}"
bin="python3 -m dotdrop.dotdrop"
if hash coverage 2>/dev/null; then
  bin="coverage run -a --source=dotdrop -m dotdrop.dotdrop"
fi

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
mkdir -p "${basedir}"/dotfiles/a/{b,c}
echo 'a' > "${basedir}"/dotfiles/a/b/abfile1
echo 'a' > "${basedir}"/dotfiles/a/b/abfile2
echo 'a' > "${basedir}"/dotfiles/a/b/abfile3
echo 'a' > "${basedir}"/dotfiles/a/c/acfile

# the dotfile to be updated
tmpd=$(mktemp -d --suffix='-dotdrop-tests' 2>/dev/null || mktemp -d)
cp -r "${basedir}"/dotfiles/a "${tmpd}"/

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"

# create the config file
cfg="${basedir}/config.yaml"
cat > "${cfg}" << _EOF
config:
  backup: false
  create: true
  dotpath: dotfiles
  upignore:
  - "*/newdir/b/*"
  - "!*/newdir/b/d"
  - "*/abfile?"
  - "!*/abfile3"
dotfiles:
  f_abc:
    dst: ${tmpd}/a
    src: a
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF

# edit/add files
echo "[+] edit/add files"
mkdir -p "${tmpd}"/a/newdir/b
echo 'b' > "${tmpd}"/a/b/abfile1
echo 'b' > "${tmpd}"/a/b/abfile2
echo 'b' > "${tmpd}"/a/b/abfile3
echo 'b' > "${tmpd}"/a/b/abfile4
touch "${tmpd}"/a/newdir/b/{c,d}

# update
echo "[+] update"
cd "${ddpath}" | ${bin} update -f -c "${cfg}" --verbose --profile=p1 --key f_abc

# check files haven't been updated
set +e
grep 'a' "${basedir}"/dotfiles/a/b/abfile1 >/dev/null 2>&1 || (echo "abfile1 should not have been updated" && exit 1)
grep 'a' "${basedir}"/dotfiles/a/b/abfile2 >/dev/null 2>&1 || (echo "abfile2 should not have been updated" && exit 1)
grep 'b' "${basedir}"/dotfiles/a/b/abfile3 >/dev/null 2>&1 || (echo "abfile3 was not updated" && exit 1)
set -e
[ -e "${basedir}"/dotfiles/a/b/abfile4 ] && echo "abfile4 should not have been updated" && exit 1
[ -e "${basedir}"/dotfiles/a/newdir/b/c ] && echo "newdir/b/c should not have been updated" && exit 1
[ ! -e "${basedir}"/dotfiles/a/newdir/b/d ] && echo "newdir/b/d should have been updated" && exit 1

echo "OK"
exit 0
