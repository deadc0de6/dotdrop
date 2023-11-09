#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2019, deadc0de6
#
# test the use of the keyword "include"
# that has to be ordered
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

# the dotfile source
tmps=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
mkdir -p "${tmps}"/dotfiles
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
# temporary
tmpa=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpa}"

export DOTDROP_WORKERS=1
# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
actions:
  pre:
    first: 'echo first > ${tmpa}/cookie'
    second: 'sleep 1; echo second >> ${tmpa}/cookie'
    third: 'sleep 1; echo third >> ${tmpa}/cookie'
dotfiles:
  f_first:
    dst: ${tmpd}/first
    src: first
    actions:
    - first
  f_second:
    dst: ${tmpd}/second
    src: second
    actions:
    - second
  f_third:
    dst: ${tmpd}/third
    src: third
    actions:
    - third
profiles:
  p0:
    dotfiles:
    - f_first
    include:
    - second
    - third
  second:
    dotfiles:
    - f_second
  third:
    dotfiles:
    - f_third
_EOF

# create the source
mkdir -p "${tmps}"/dotfiles/
echo "first" > "${tmps}"/dotfiles/first
sleep 1
echo "second" > "${tmps}"/dotfiles/second
sleep 1
echo "third" > "${tmps}"/dotfiles/third

attempts="3"
for ((i=0;i<attempts;i++)); do
  # install
  cd "${ddpath}" | ${bin} install -w 1 -f -c "${cfg}" -p p0 -V

  # checks timestamp
  echo "first timestamp: $(stat -c %y "${tmpd}"/first)"
  echo "second timestamp: $(stat -c %y "${tmpd}"/second)"
  echo "third timestamp: $(stat -c %y "${tmpd}"/third)"

  ts_first=$(date "+%s" -d "$(stat -c %y "${tmpd}"/first)")
  ts_second=$(date "+%s" -d "$(stat -c %y "${tmpd}"/second)")
  ts_third=$(date "+%s" -d "$(stat -c %y "${tmpd}"/third)")

  #echo "first ts: ${ts_first}"
  #echo "second ts: ${ts_second}"
  #echo "third ts: ${ts_third}"

  [ "${ts_first}" -ge "${ts_second}" ] && echo "second created before first" && exit 1
  [ "${ts_second}" -ge "${ts_third}" ] && echo "third created before second" && exit 1

  # check cookie
  cat "${tmpa}"/cookie
  content=$(cat "${tmpa}"/cookie | xargs)
  [ "${content}" != "first second third" ] && echo "bad cookie" && exit 1

  # clean
  rm "${tmpa}"/cookie
  rm "${tmpd}"/first "${tmpd}"/second "${tmpd}"/third
done

echo "OK"
exit 0
