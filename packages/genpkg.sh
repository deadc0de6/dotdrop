#!/bin/bash
# author: deadc0de6
#
# update packages
#

# $1: version
up()
{
  # update pkgver
  [ "${1}" != "" ] && sed -i "s/^pkgver=.*$/pkgver=${1}/g" "${pkgfile}"
  # create srcinfo
  rm -f .SRCINFO
  makepkg --printsrcinfo > .SRCINFO
}

# pivot
rl="readlink -f"
if ! ${rl} "${0}" >/dev/null 2>&1; then
  rl="realpath"

  if ! hash ${rl}; then
    echo "\"${rl}\" not found!" && exit 1
  fi
fi
# cur
cur=$(dirname "$(${rl} "${0}")")
opwd=$(pwd)
pkgfile="PKGBUILD"
cd "${cur}" || exit 1

########################
# update arch package
# tag release
########################
dir="arch-dotdrop"
echo "doing ${dir} ..."
cd ${dir} || exit 1
version="$(git describe --abbrev=0 --tags | sed 's/^v//g')"
up "${version}"
cd "${OLDPWD}" || exit 1

#########################
## update arch package
## git release
#########################
#dir="arch-dotdrop-git"
#echo "doing ${dir} ..."
#cd ${dir}
## replace pkgver
##version="`git describe --long --tags | sed 's/\([^-]*-g\)/r\1/;s/-/./g;s/^v//g'`"
#up
#cd ${OLDPWD}

# pivot back
cd "${opwd}" || exit
