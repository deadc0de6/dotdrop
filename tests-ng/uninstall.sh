#!/usr/bin/env bash
# author: deadc0de6 (https://github.com/deadc0de6)
# Copyright (c) 2023, deadc0de6
#
# test uninstall (no symlink)
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
# $1 pattern
# $2 path
grep_or_fail()
{
  if ! grep "${1}" "${2}" >/dev/null 2>&1; then
    echo "${PRE} pattern \"${1}\" not found in ${2}"
    exit 1
  fi
}

# $1: basedir
# $2: content
create_hierarchy()
{
  echo "${2}" > "${1}"/x
  mkdir -p "${1}"/y
  echo "${2}" > "${1}"/y/file
  mkdir -p "${1}"/y/subdir
  echo "${2}" > "${1}"/y/subdir/subfile
  echo "profile: ${PRO_TEMPL}" > "${1}"/t
  mkdir -p "${1}"/z
  echo "profile t1: ${PRO_TEMPL}" > "${1}"/z/t1
  echo "profile t2: ${PRO_TEMPL}" > "${1}"/z/t2
  echo "${2}" > "${1}"/z/file
  echo "trans:${PRO_TEMPL}" > "${1}"/trans
}

# $1: basedir
clean_hierarchy()
{
  rm -rf "${1:?}"/*
}

uninstall_with_link()
{
  set -e

  LINK_TYPE="${DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE:-nolink}"
  PRE="[link:${LINK_TYPE}] ERROR"
  PRO_TEMPL="{{@@ profile @@}}"
  DT_ARG="--verbose"

  # dotdrop directory
  basedir=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
  mkdir -p "${basedir}"/dotfiles
  echo "[+] dotdrop dir: ${basedir}"
  echo "[+] dotpath dir: ${basedir}/dotfiles"
  tmpd=$(mktemp -d --suffix='-dotdrop-tests' || mktemp -d)
  tmpw=$(mktemp -d --suffix='-dotdrop-workdir' || mktemp -d)

  clear_on_exit "${basedir}/dotfiles"
  clear_on_exit "${tmpd}"
  clear_on_exit "${tmpw}"

  file_link="${LINK_TYPE}"
  dir_link="${LINK_TYPE}"
  if [ "${LINK_TYPE}" = "link_children" ]; then
    file_link="absolute"
  fi

  # create the config file
  cfg="${basedir}/config.yaml"
  cat > "${cfg}" << _EOF
config:
  backup: true
  create: true
  dotpath: dotfiles
  link_dotfile_default: ${LINK_TYPE}
  workdir: ${tmpw}
dotfiles:
  f_x:
    src: x
    dst: ${tmpd}/x
    link: ${file_link}
  d_y:
    src: y
    dst: ${tmpd}/y
    link: ${dir_link}
  f_t:
    src: t
    dst: ${tmpd}/t
    link: ${file_link}
  d_z:
    src: z
    dst: ${tmpd}/z
    link: ${dir_link}
  f_trans:
    src: trans
    dst: ${tmpd}/trans
    link: ${file_link}
profiles:
  p1:
    dotfiles:
    - f_x
    - d_y
    - f_t
    - d_z
    - f_trans
_EOF

  #########################
  ## no original
  #########################

  create_hierarchy "${basedir}/dotfiles" "modified"

  # install
  echo "[+] install (1)"
  ( \
    cd "${ddpath}" && ${bin} install -c "${cfg}" -f -p p1 | grep '^4 dotfile(s) installed.$' \
  )

  # tests
  [ ! -e "${tmpd}"/x ] && echo "${PRE} f_x not installed" && exit 1
  [ ! -e "${tmpd}"/y/file ] && echo "${PRE} d_y not installed" && exit 1
  [ ! -e "${tmpd}"/y/subdir/subfile ] && echo "${PRE} d_y not installed" && exit 1
  [ ! -e "${tmpd}"/t ] && echo "${PRE} f_t not installed" && exit 1
  [ ! -e "${tmpd}"/z/t1 ] && echo "${PRE} d_z t1 not installed" && exit 1
  [ ! -e "${tmpd}"/z/t2 ] && echo "${PRE} d_z t2 not installed" && exit 1
  [ ! -e "${tmpd}"/z/file ] && echo "${PRE} d_z file not installed" && exit 1
  [ ! -e "${tmpd}"/trans ] && echo "${PRE} f_trans file not installed" && exit 1
  grep_or_fail 'modified' "${tmpd}"/x
  grep_or_fail 'modified' "${tmpd}"/y/file
  grep_or_fail 'profile: p1' "${tmpd}"/t
  grep_or_fail 'profile t1: p1' "${tmpd}"/z/t1
  grep_or_fail 'profile t2: p1' "${tmpd}"/z/t2
  grep_or_fail 'modified' "${tmpd}"/z/file
  grep_or_fail 'trans:p1' "${tmpd}"/trans

  # uninstall
  echo "[+] uninstall (1)"
  ( \
    cd "${ddpath}" && ${bin} uninstall -c "${cfg}" -f -p p1 "${DT_ARG}" \
  )
  [ "$?" != "0" ] && exit 1

  # tests
  [ ! -d "${basedir}"/dotfiles ] && echo "${PRE} dotpath removed" && exit 1
  [ -e "${tmpd}"/x ] && echo "${PRE} f_x not uninstalled" && exit 1
  [ -d "${tmpd}"/y ] && echo "${PRE} d_y dir not uninstalled" && exit 1
  [ -e "${tmpd}"/y/file ] && echo "${PRE} d_y file not uninstalled" && exit 1
  [ -e "${tmpd}"/y/subdir/subfile ] && echo "${PRE} d_y subfile not uninstalled" && exit 1
  [ -e "${tmpd}"/t ] && echo "${PRE} f_t not uninstalled" && exit 1
  [ -e "${tmpd}"/z/t1 ] && echo "${PRE} d_z subfile t1 not uninstalled" && exit 1
  [ -e "${tmpd}"/z/t2 ] && echo "${PRE} d_z subfile t2 not uninstalled" && exit 1
  [ -e "${tmpd}"/z/file ] && echo "${PRE} d_z subfile file not uninstalled" && exit 1
  [ -e "${tmpd}"/trans ] && echo "${PRE} f_trans file not uninstalled" && exit 1

  # test workdir is empty
  if [ -n "$(ls -A "${tmpw}")" ]; then
    echo "${PRE} workdir (1) is not empty"
    echo "---"
    ls -A "${tmpw}"
    echo "---"
    exit 1
  fi

  #########################
  ## with original
  #########################
  # clean
  clean_hierarchy "${tmpd}"
  clean_hierarchy "${basedir}"/dotfiles

  # recreate
  create_hierarchy "${basedir}"/dotfiles "modified"
  create_hierarchy "${tmpd}" "original"

  # install
  echo "[+] install (2)"
  cd "${ddpath}" | ${bin} install -c "${cfg}" -f -p p1 | grep '^4 dotfile(s) installed.$'

  # tests
  [ ! -e "${tmpd}"/x ] && echo "${PRE} f_x not installed" && exit 1
  [ ! -e "${tmpd}"/x.dotdropbak ] && echo "${PRE} f_x backup not created" && exit 1
  [ ! -d "${tmpd}"/y ] && echo "${PRE} d_y not installed" && exit 1
  [ ! -e "${tmpd}"/y/file ] && echo "${PRE} d_y file not installed" && exit 1
  [ "${LINK_TYPE}" = "nolink" ] && [ ! -e "${tmpd}"/y/file.dotdropbak ] && echo "${PRE} d_y backup file not created" && exit 1
  [ ! -e "${tmpd}"/y/subdir/subfile ] && echo "${PRE} d_y subfile not installed" && exit 1
  [ "${LINK_TYPE}" = "nolink" ] && [ ! -e "${tmpd}"/y/subdir/subfile.dotdropbak ] && echo "${PRE} d_y subfile backup not created" && exit 1
  [ ! -e "${tmpd}"/t ] && echo "${PRE} f_t not installed" && exit 1
  [ ! -e "${tmpd}"/t.dotdropbak ] && echo "${PRE} f_t backup not created" && exit 1
  [ ! -e "${tmpd}"/z/t1 ] && echo "${PRE} d_z t1 not installed" && exit 1
  [ "${LINK_TYPE}" = "nolink" ] && [ ! -e "${tmpd}"/z/t1.dotdropbak ] && echo "${PRE} d_z t1 backup not created" && exit 1
  [ ! -e "${tmpd}"/z/t2 ] && echo "${PRE} d_z t2 not installed" && exit 1
  [ "${LINK_TYPE}" = "nolink" ] && [ ! -e "${tmpd}"/z/t2.dotdropbak ] && echo "${PRE} d_z t2 backup not created" && exit 1
  [ ! -e "${tmpd}"/z/file ] && echo "${PRE} d_z file not installed" && exit 1
  [ "${LINK_TYPE}" = "nolink" ] && [ ! -e "${tmpd}"/z/file.dotdropbak ] && echo "${PRE} d_z backup file not created" && exit 1
  [ ! -e "${tmpd}"/trans ] && echo "${PRE} f_trans file not installed" && exit 1
  [ ! -e "${tmpd}"/trans.dotdropbak ] && echo "${PRE} f_trans backup file not created" && exit 1
  grep_or_fail 'modified' "${tmpd}"/x
  grep_or_fail 'modified' "${tmpd}"/y/file
  grep_or_fail 'profile: p1' "${tmpd}"/t
  grep_or_fail 'profile t1: p1' "${tmpd}"/z/t1
  grep_or_fail 'profile t2: p1' "${tmpd}"/z/t2
  grep_or_fail 'modified' "${tmpd}"/z/file
  grep_or_fail 'trans:p1' "${tmpd}"/trans

  # uninstall
  echo "[+] uninstall (2)"
  ( \
    cd "${ddpath}" && ${bin} uninstall -c "${cfg}" -f -p p1 "${DT_ARG}" \
  )
  [ "$?" != "0" ] && exit 1

  # tests
  [ ! -d "${basedir}"/dotfiles ] && echo "${PRE} dotpath removed" && exit 1
  [ ! -e "${tmpd}"/x ] && echo "${PRE} f_x backup not restored" && exit 1
  [ -e "${tmpd}"/x.dotdropbak ] && echo "${PRE} f_x backup not removed" && exit 1
  [ "${LINK_TYPE}" = "nolink" ] && [ ! -d "${tmpd}"/y ] && echo "${PRE} d_y backup not restored" && exit 1
  [ "${LINK_TYPE}" = "nolink" ] && [ ! -e "${tmpd}"/y/file ] && echo "${PRE} d_y file backup not restored" && exit 1
  [ -e "${tmpd}"/y/file.dotdropbak ] && echo "${PRE} d_y backup not removed" && exit 1
  [ "${LINK_TYPE}" = "nolink" ] && [ ! -e "${tmpd}"/y/subdir/subfile ] && echo "${PRE} d_y sub backup not restored" && exit 1
  [ -e "${tmpd}"/y/subdir/subfile.dotdropbak ] && echo "${PRE} d_y sub backup not removed" && exit 1
  [ ! -e "${tmpd}"/t ] && echo "${PRE} f_t not restored" && exit 1
  [ -e "${tmpd}"/t.dotdropbak ] && echo "${PRE} f_t backup not removed" && exit 1
  [ "${LINK_TYPE}" = "nolink" ] && [ ! -e "${tmpd}"/z/t1 ] && echo "${PRE} d_z t1 not restore" && exit 1
  [ -e "${tmpd}"/z/t1.dotdropbak ] && echo "${PRE} d_z t1 backup not removed" && exit 1
  [ "${LINK_TYPE}" = "nolink" ] && [ ! -e "${tmpd}"/z/t2 ] && echo "${PRE} d_z t2 not restored" && exit 1
  [ -e "${tmpd}"/z/t2.dotdropbak ] && echo "${PRE} d_z t2 backup not removed" && exit 1
  [ "${LINK_TYPE}" = "nolink" ] && [ ! -e "${tmpd}"/z/file ] && echo "${PRE} d_z file not restored" && exit 1
  [ -e "${tmpd}"/z/file.dotdropbak ] && echo "${PRE} d_z file backup not removed" && exit 1
  [ ! -e "${tmpd}"/trans ] && echo "${PRE} f_trans backup not restored" && exit 1
  [ -e "${tmpd}"/trans.dotdropbak ] && echo "${PRE} f_trans backup not removed" && exit 1

  grep_or_fail 'original' "${tmpd}"/x
  [ "${LINK_TYPE}" = "nolink" ] && grep_or_fail 'original' "${tmpd}"/y/file
  grep_or_fail "profile: ${PRO_TEMPL}" "${tmpd}/t"
  [ "${LINK_TYPE}" = "nolink" ] && grep_or_fail "profile t1: ${PRO_TEMPL}" "${tmpd}/z/t1"
  [ "${LINK_TYPE}" = "nolink" ] && grep_or_fail "profile t2: ${PRO_TEMPL}" "${tmpd}/z/t2"
  [ "${LINK_TYPE}" = "nolink" ] && grep_or_fail 'original' "${tmpd}"/z/file
  grep_or_fail "trans:${PRO_TEMPL}" "${tmpd}"/trans

  echo "testing workdir..."

  # test workdir is empty
  if [ -n "$(ls -A "${tmpw}")" ]; then
    echo "${PRE} workdir (2) - ${tmpw} - is not empty"
    ls -r "${tmpw}"
    exit 1
  fi

  echo "${PRE} done OK"
}

export DOTDROP_TEST_NG_UNINSTALL_DDPATH="${ddpath}"
export DOTDROP_TEST_NG_UNINSTALL_BIN="${bin}"
export DOTDROP_TEST_NG_CUR="${cur}"

export DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE="nolink"
# shellcheck source=uninstall_
echo "[+] testing uninstall link:${DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE}..."
if ! uninstall_with_link; then exit 1; fi
echo "[+] uninstall link:${DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE} OK"

export DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE="absolute"
# shellcheck source=uninstall_
echo "[+] testing uninstall link:${DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE}..."
if ! uninstall_with_link; then exit 1; fi
echo "[+] uninstall link:${DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE} OK"

export DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE="relative"
# shellcheck source=uninstall_
echo "[+] testing uninstall link:${DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE}..."
if ! uninstall_with_link; then exit 1; fi
echo "[+] uninstall link:${DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE} OK"

export DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE="link_children"
# shellcheck source=uninstall_
echo "[+] testing uninstall link:${DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE}..."
if ! uninstall_with_link; then exit 1; fi
echo "[+] uninstall link:${DOTDROP_TEST_NG_UNINSTALL_LINK_TYPE} OK"

echo "OK"
exit 0