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

cat "${cfg}"

# ensure exists and is not link
[ ! -d "${tmps}"/dotfiles/"${tmpd}"/adir ] && echo "not a directory" && exit 1
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/adir/file1 ] && echo "not exist" && exit 1
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/adir/file2 ] && echo "not exist" && exit 1
[ ! -e "${tmps}"/dotfiles/"${tmpd}"/file3 ] && echo "not a file" && exit 1

cat "${cfg}" | grep "${tmpd}"/adir >/dev/null 2>&1
cat "${cfg}" | grep "${tmpd}"/file3 >/dev/null 2>&1

nb=$(cat "${cfg}" | grep d_adir | wc -l)
[ "${nb}" != "2" ] && echo 'bad config1' && exit 1
nb=$(cat "${cfg}" | grep f_file3 | wc -l)
[ "${nb}" != "2" ] && echo 'bad config2' && exit 1

cntpre=$(find "${tmps}"/dotfiles -type f | wc -l)

# reimport
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V "${tmpd}"/adir
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p1 -V "${tmpd}"/file3

cntpost=$(find "${tmps}"/dotfiles -type f | wc -l)

[ "${cntpost}" != "${cntpre}" ] && echo "import issue" && exit 1

#######################################
# import directory with named pipe

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
profiles:
_EOF

# create the dotfile
d="${tmpd}/with_named_pipe"
mkdir -p "${d}"
echo "file1" > "${d}"/file1
echo "fil2" > "${d}"/file2
mkfifo "${d}"/fifo

# import
cd "${ddpath}" | ${bin} import -f -c "${cfg}" -p p2 -V "${d}"

# ensure exists and is not link
[ ! -d "${tmps}"/dotfiles/"${d}" ] && echo "not a directory" && exit 1
[ ! -e "${tmps}"/dotfiles/"${d}"/file1 ] && echo "not exist" && exit 1
[ ! -e "${tmps}"/dotfiles/"${d}"/file2 ] && echo "not exist" && exit 1

cat "${cfg}" | grep "${d}" >/dev/null 2>&1

echo "OK"
exit 0
