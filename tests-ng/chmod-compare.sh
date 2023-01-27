#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2020, deadc0de6
#
# test chmod on compare
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

#hash dotdrop >/dev/null 2>&1
#[ "$?" != "0" ] && echo "install dotdrop to run tests" && exit 1

#echo "called with ${1}"

# dotdrop path can be pass as argument
ddpath="${cur}/../"
[ "${1}" != "" ] && ddpath="${1}"
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

# the dotfile source
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create the dotfile
dnormal="${tmpd}/dir_normal"
mkdir -p "${dnormal}"
echo "dir_normal/f1" > "${dnormal}"/file1
echo "dir_normal/f2" > "${dnormal}"/file2
chmod 777 "${dnormal}"

dlink="${tmpd}/dir_link"
mkdir -p "${dlink}"
echo "dir_link/f1" > "${dlink}"/file1
echo "dir_link/f2" > "${dlink}"/file2
chmod 777 "${dlink}"

dlinkchildren="${tmpd}/dir_link_children"
mkdir -p "${dlinkchildren}"
echo "dir_linkchildren/f1" > "${dlinkchildren}"/file1
echo "dir_linkchildren/f2" > "${dlinkchildren}"/file2
chmod 777 "${dlinkchildren}"

fnormal="${tmpd}/filenormal"
echo "filenormal" > "${fnormal}"
chmod 777 "${fnormal}"

flink="${tmpd}/filelink"
echo "filelink" > "${flink}"
chmod 777 "${flink}"

echo "f777" > "${tmps}"/dotfiles/f777
chmod 700 "${tmps}"/dotfiles/f777

toimport="${dnormal} ${dlink} ${dlinkchildren} ${fnormal} ${flink}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
dotfiles:
  f_f777:
    src: f777
    dst: ${tmpd}/f777
    chmod: 777
profiles:
  p1:
    dotfiles:
    - f_f777
_EOF
#cat ${cfg}

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1

# compare
cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1

# import
for i in ${toimport}; do
  cd "${ddpath}" | ${bin} import -c "${cfg}" -f -p p1 "${i}"
done

#cat ${cfg}

# patch rights
chmod 700 "${dnormal}"
chmod 700 "${dlink}"
chmod 700 "${dlinkchildren}"
chmod 700 "${fnormal}"
chmod 700 "${flink}"

set +e
out=$(cd "${ddpath}" | ${bin} compare -c "${cfg}" -p p1 2>&1)
cnt=$(echo "${out}" | grep 'modes differ' | wc -l)
set -e
[ "${cnt}" != "5" ] && echo "${out}" && echo "compare modes failed (${cnt}, expecting 5)" && exit 1

echo "OK"
exit 0
