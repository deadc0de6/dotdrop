#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test basic import
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

# the dotfile source
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${HOME}/.dotdrop.test"
clear_on_exit "${HOME}/.dotdrop-dotfiles-test"

# create the dotfile
mkdir -p "${tmpd}"/adir
echo "adir/file1" > "${tmpd}"/adir/file1
echo "adir/fil2" > "${tmpd}"/adir/file2
echo "file3" > "${tmpd}"/file3

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF
#cat ${cfg}

# import
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V "${tmpd}"/adir
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V "${tmpd}"/file3

echo "import --as dotfiles"
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p2 -V "${tmpd}"/adir --as ~/config/adir
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p2 -V "${tmpd}"/file3 --as ~/config2/file3

cat "${cfg}"

set +e
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p2 -V "${tmpd}"/adir --as ~/config/should_not && echo "dual dst imported" && exit 1
set -e
cat "${cfg}" | grep should_not && echo "dual dst imported" && exit 1

cat "${cfg}"

echo "ensure exists and is not link"
[ ! -d "${tmps}"/dotfiles/"${tmpd}"/adir ] && echo "not a directory" && exit 1
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/adir/file1 ] && echo "not exist" && exit 1
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/adir/file2 ] && echo "not exist" && exit 1
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/file3 ] && echo "not a file" && exit 1

echo "ensure --as are correctly imported"
[ ! -d "${tmps}"/dotfiles/config/adir ] && echo "not a directory" && exit 1
[ ! -e "${tmps}"/dotfiles/config/adir/file1 ] && echo "not exist" && exit 1
[ ! -e "${tmps}"/dotfiles/config/adir/file2 ] && echo "not exist" && exit 1
[ ! -e "${tmps}"/dotfiles/config2/file3 ] && echo "not a file" && exit 1

cat "${cfg}" | grep "${tmpd}"/adir >/dev/null 2>&1
cat "${cfg}" | grep "${tmpd}"/file3 >/dev/null 2>&1

cat "${cfg}" | grep config/adir >/dev/null 2>&1
cat "${cfg}" | grep config2/file3 >/dev/null 2>&1

nb=$(cat "${cfg}" | grep d_adir | wc -l)
[ "${nb}" != "2" ] && echo 'bad config1' && exit 1
nb=$(cat "${cfg}" | grep f_file3 | wc -l)
[ "${nb}" != "2" ] && echo 'bad config2' && exit 1

cat "${cfg}" | grep "src: config/adir" || exit 1
cat "${cfg}" | grep "src: config2/file3" || exit 1

# test import from sub in home
mkdir -p ~/.dotdrop-dotfiles-test/{dotfiles,config}
cfg=~/.dotdrop-dotfiles-test/config/config.yaml
echo 'remove-me' > ~/.dotdrop.test
cat > ${cfg} << _EOF
config:
  backup: true
  banner: true
  create: true
  dotpath: ~/.dotdrop-dotfiles-test/dotfiles
  keepdot: false
  link_dotfile_default: nolink
  link_on_import: nolink
  longkey: true
dotfiles:
profiles:
_EOF

cd "${ddpath}" | ${bin} import -f -b -c ${cfg} -p test -V ~/.dotdrop.test --as=~/.whatever
#cat ${cfg}

[ ! -e ~/.dotdrop-dotfiles-test/dotfiles/whatever ] && echo 'tild imported' && exit 1
cat ${cfg} | grep "${HOME}/.whatever" && echo 'import with tild failed' && exit 1

echo "OK"
exit 0
