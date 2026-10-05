#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2026, deadc0de6
#
# test --prompt/--no-prompt and the prompt config entry
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
mkdir -p "${basedir}"/dotfiles
tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
tmpw=$(mktemp -d --suffix='-dotdrop-workdir' || mktemp -d)

clear_on_exit "${basedir}"
clear_on_exit "${tmpd}"
clear_on_exit "${tmpw}"

echo "content" > "${basedir}"/dotfiles/x
echo "content" > "${basedir}"/dotfiles/y

write_cfg()
{
  local prompt_val="${1}"
  cat > "${basedir}/config.yaml" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  workdir: ${tmpw}
  prompt: ${prompt_val}
dotfiles:
  f_x:
    src: x
    dst: ${tmpd}/x
  f_y:
    src: y
    dst: ${tmpd}/y
profiles:
  p1:
    dotfiles:
    - f_x
    - f_y
_EOF
}

# ------------------------------------------------
# 1. prompt:true + answer "n" -> nothing installed
# ------------------------------------------------
write_cfg "true"
rm -f "${tmpd}"/x "${tmpd}"/y

echo "[+] prompt:true, answer n (abort)"
out=$(printf "n\n" | ${bin} -c "${basedir}/config.yaml" -p p1 install 2>&1 || true)
echo "${out}" | grep -q 'would be applied by install' \
  || (echo "preview header missing" && exit 1)
echo "${out}" | grep -q 'Apply these changes?' \
  || (echo "confirmation question missing" && exit 1)
echo "${out}" | grep -q 'install aborted.' \
  || (echo "abort message missing" && exit 1)
[ -e "${tmpd}"/x ] && echo "x should not exist (abort)" && exit 1
[ -e "${tmpd}"/y ] && echo "y should not exist (abort)" && exit 1

# ------------------------------------------------
# 2. prompt:true + answer "y" -> installed
# ------------------------------------------------
echo "[+] prompt:true, answer y (proceed)"
out=$(printf "y\n" | ${bin} -c "${basedir}/config.yaml" -p p1 install 2>&1 || true)
echo "${out}" | grep -q '2 dotfile(s) installed.' \
  || (echo "install summary missing" && exit 1)
[ ! -e "${tmpd}"/x ] && echo "x not installed" && exit 1
[ ! -e "${tmpd}"/y ] && echo "y not installed" && exit 1

# ------------------------------------------------
# 3. prompt:true + --no-prompt -> no preview, direct install
# ------------------------------------------------
rm -f "${tmpd}"/x "${tmpd}"/y
echo "[+] prompt:true + --no-prompt (no preview, direct install)"
out=$(${bin} -c "${basedir}/config.yaml" -p p1 --no-prompt install 2>&1 || true)
echo "${out}" | grep -q 'would be applied by install' \
  && echo "preview should NOT be shown with --no-prompt" && exit 1
echo "${out}" | grep -q 'Apply these changes?' \
  && echo "question should NOT be shown with --no-prompt" && exit 1
echo "${out}" | grep -q '2 dotfile(s) installed.' \
  || (echo "install summary missing" && exit 1)
[ ! -e "${tmpd}"/x ] && echo "x not installed" && exit 1
[ ! -e "${tmpd}"/y ] && echo "y not installed" && exit 1

# ------------------------------------------------
# 4. prompt:false + --prompt + answer "n" -> aborted
# ------------------------------------------------
write_cfg "false"
rm -f "${tmpd}"/x "${tmpd}"/y
echo "[+] prompt:false + --prompt, answer n (abort)"
out=$(printf "n\n" | ${bin} -c "${basedir}/config.yaml" -p p1 --prompt install 2>&1 || true)
echo "${out}" | grep -q 'would be applied by install' \
  || (echo "preview header missing" && exit 1)
echo "${out}" | grep -q 'install aborted.' \
  || (echo "abort message missing" && exit 1)
[ -e "${tmpd}"/x ] && echo "x should not exist (abort)" && exit 1
[ -e "${tmpd}"/y ] && echo "y should not exist (abort)" && exit 1

# ------------------------------------------------
# 5. prompt:false (default) -> no prompt, direct install
# ------------------------------------------------
rm -f "${tmpd}"/x "${tmpd}"/y
echo "[+] prompt:false default (no prompt)"
out=$(${bin} -c "${basedir}/config.yaml" -p p1 install 2>&1 || true)
echo "${out}" | grep -q 'would be applied by install' \
  && echo "preview should NOT be shown when prompt disabled" && exit 1
echo "${out}" | grep -q '2 dotfile(s) installed.' \
  || (echo "install summary missing" && exit 1)
[ ! -e "${tmpd}"/x ] && echo "x not installed" && exit 1
[ ! -e "${tmpd}"/y ] && echo "y not installed" && exit 1

# ------------------------------------------------
# 6. prompt:true + --force -> no prompt, direct install
# ------------------------------------------------
write_cfg "true"
rm -f "${tmpd}"/x "${tmpd}"/y
echo "[+] prompt:true + --force (no prompt)"
out=$(${bin} -c "${basedir}/config.yaml" -p p1 -f install 2>&1 || true)
echo "${out}" | grep -q 'would be applied by install' \
  && echo "preview should NOT be shown with --force" && exit 1
echo "${out}" | grep -q '2 dotfile(s) installed.' \
  || (echo "install summary missing" && exit 1)
[ ! -e "${tmpd}"/x ] && echo "x not installed" && exit 1
[ ! -e "${tmpd}"/y ] && echo "y not installed" && exit 1

# ------------------------------------------------
# 7. uninstall with prompt:true + answer "n"
# ------------------------------------------------
write_cfg "true"
# make sure files exist (installed)
[ ! -e "${tmpd}"/x ] && echo "content" > "${tmpd}"/x
[ ! -e "${tmpd}"/y ] && echo "content" > "${tmpd}"/y
echo "[+] uninstall prompt:true, answer n (abort)"
out=$(printf "n\n" | ${bin} -c "${basedir}/config.yaml" -p p1 uninstall 2>&1 || true)
echo "${out}" | grep -q 'would be applied by uninstall' \
  || (echo "preview header missing" && exit 1)
echo "${out}" | grep -q 'uninstall aborted.' \
  || (echo "abort message missing" && exit 1)
[ ! -e "${tmpd}"/x ] && echo "x should still exist (abort)" && exit 1
[ ! -e "${tmpd}"/y ] && echo "y should still exist (abort)" && exit 1

# ------------------------------------------------
# 8. uninstall with prompt:true + answer "y"
# ------------------------------------------------
echo "[+] uninstall prompt:true, answer y (proceed)"
out=$(printf "y\n" | ${bin} -c "${basedir}/config.yaml" -p p1 uninstall 2>&1 || true)
echo "${out}" | grep -q '2 dotfile(s) uninstalled.' \
  || (echo "uninstall summary missing" && exit 1)
[ -e "${tmpd}"/x ] && echo "x should be removed" && exit 1
[ -e "${tmpd}"/y ] && echo "y should be removed" && exit 1

echo "OK"
exit 0
