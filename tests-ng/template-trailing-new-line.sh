#!/usr/bin/env bash
# author: deadc0de6
#
# test trailing new line for
# https://github.com/deadc0de6/dotdrop/issues/438
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
echo "dotfiles source (dotpath): ${tmps}"
# the dotfile destination
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
echo "dotfiles destination: ${tmpd}"
# the workdir
tmpw=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
export DOTDROP_WORKDIR="${tmpw}"
echo "workdir: ${tmpw}"

clear_on_exit "${tmps}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpw}"

# create the config file
cfg="${tmps}/config.yaml"

cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  workdir: ${tmpw}
dotfiles:
  f_abc:
    dst: ${tmpd}/abc
    src: abc
variables:
  profilexx: ""
  var_RJC_pinotu___51e1db5e: ""
  var____8dc4b111: "# "
  var____fbe9a844: "#"
  var__ifaRCpns_imf1__5c8ecb88: ""
profiles:
  p1:
    dotfiles:
    - f_abc
  profile2_def:
    dotfiles:
    - f_abc
_EOF
#cat ${cfg}

# create the dotfile
cat > "${tmps}"/dotfiles/abc << _EOF
{{@@ profile @@}}

_EOF

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b -V

echo "---"
cat "${tmpd}/abc"
echo "---"

# checks
[ ! -e "${tmpd}"/abc ] && echo "[ERROR] dotfile not installed" && exit 1
nbline=$(wc -l "${tmpd}/abc" | awk '{print $1}')
[ "${nbline}" != 2 ] && (echo "[ERROR] trailing new line stripped (${nbline})"; exit 1)

# clear
rm -f "${tmpd}/abc"

# create the dotfile
cat > "${tmps}"/dotfiles/abc << _EOF
{{@@ profile @@}}
_EOF

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b -V

# checks
[ ! -e "${tmpd}"/abc ] && echo "[ERROR] dotfile not installed" && exit 1
nbline=$(wc -l "${tmpd}/abc" | awk '{print $1}')
[ "${nbline}" != 1 ] && (echo "[ERROR] trailing new line stripped"; exit 1)

# clear
rm -f "${tmpd}/abc"

# create the dotfile
cat > "${tmps}"/dotfiles/abc << _EOF
{{@@ profilexx @@}}

_EOF

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b -V

echo "---"
cat "${tmpd}/abc"
echo "---"

# checks
[ ! -e "${tmpd}"/abc ] && echo "[ERROR] dotfile not installed" && exit 1
nbline=$(wc -l "${tmpd}/abc" | awk '{print $1}')
[ "${nbline}" != 2 ] && (echo "[ERROR] trailing new line stripped"; exit 1)

# clear
rm -f "${tmpd}/abc"

# create the dotfile
cat > "${tmps}"/dotfiles/abc << _EOF
{{@@+ profilexx @@}}

_EOF

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p p1 -b -V

echo "---"
cat "${tmpd}/abc"
echo "---"

# checks
[ ! -e "${tmpd}"/abc ] && echo "[ERROR] dotfile not installed" && exit 1
nbline=$(wc -l "${tmpd}/abc" | awk '{print $1}')
[ "${nbline}" != 2 ] && (echo "[ERROR] trailing new line stripped"; exit 1)

# clear
rm -f "${tmpd}/abc"

# create the dotfile
cat > "${tmps}"/dotfiles/abc << _EOF
config zone
	option name		wan
	{{@@+ var____8dc4b111 @@}}list   network		'wan'
  {%@@+ if profile == "profile1abc" @@%}{%@@+ elif profile == "profile2_def" @@%}
  option	network		'wan wan6'
	option input		DROP
	option output		ACCEPT
	option forward		DROP
	option masq		1
	option mtu_fix		1
    option log 1
    option log_limit '2/minute'
# option family 'ipv4'

#config zone
#	option name		wan6
{%@@+ endif @@%}
#	list   network		'wan6'
{{@@+ var____fbe9a844 @@}}	option input		{{@@+ var_RJC_pinotu___51e1db5e @@}}ACCEPT{{@@+ var__ifaRCpns_imf1__5c8ecb88 @@}}
_EOF

# install
cd "${ddpath}" | ${bin} install -f -c "${cfg}" -p profile2_def -b -V

echo "---"
cat "${tmpd}/abc"
echo "---"

cat << _EOF > "${tmpd}/expected"
config zone
	option name		wan
	# list   network		'wan'
    option	network		'wan wan6'
	option input		DROP
	option output		ACCEPT
	option forward		DROP
	option masq		1
	option mtu_fix		1
    option log 1
    option log_limit '2/minute'
# option family 'ipv4'

#config zone
#	option name		wan6
#	list   network		'wan6'
#	option input		ACCEPT
_EOF

# checks
[ ! -e "${tmpd}"/abc ] && echo "[ERROR] dotfile not installed" && exit 1
echo "diffing..."
if ! diff "${tmpd}/abc" "${tmpd}/expected"; then
  echo "[ERROR] unmatched content"
  exit 1
fi

echo "OK"
exit 0