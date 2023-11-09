#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2017, deadc0de6
#
# test dynamic variables from yaml file
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
#echo "dotfile destination: ${tmpd}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"

# create a shell script
export TESTENV="this is my testenv"
scr=$(mktemp --suffix='-dotdrop-tests' || mktemp -d)
chmod +x "${scr}"
echo -e "#!/usr/bin/env bash\necho $TESTENV\n" >> "${scr}"
clear_on_exit "${scr}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
variables:
  var1: "this is some test"
  var2: "the_dvar4"
dynvariables:
  dvar1: head -1 ${cur}/helpers
  dvar2: "echo 'this is some test' | rev | tr ' ' ','"
  dvar3: ${scr}
  dvar4: "echo {{@@ var2 @@}} | rev"
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
profiles:
  p1:
    dotfiles:
    - f_abc
_EOF
#cat "${cfg}"

# create the dotfile
echo "{{@@ var1 @@}}" > "${tmps}"/dotfiles/abc
echo "{{@@ dvar1 @@}}" >> "${tmps}"/dotfiles/abc
echo "{{@@ dvar2 @@}}" >> "${tmps}"/dotfiles/abc
echo "{{@@ dvar3 @@}}" >> "${tmps}"/dotfiles/abc
echo "{{@@ dvar4 @@}}" >> "${tmps}"/dotfiles/abc
echo "test" >> "${tmps}"/dotfiles/abc

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -V

#cat "${cfg}"
echo "-----"
cat "${tmpd}"/abc
echo "-----"

grep '^this is some test' "${tmpd}"/abc >/dev/null
grep '^# shellcheck' "${tmpd}"/abc >/dev/null
grep '^tset,emos,si,siht' "${tmpd}"/abc >/dev/null
grep "^${TESTENV}" "${tmpd}"/abc > /dev/null
grep '^4ravd_eht' "${tmpd}"/abc >/dev/null

#cat ${tmpd}/abc

echo "OK"
exit 0
