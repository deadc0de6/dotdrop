# Maintainer: deadc0de6 <info@deadc0de.ch>

_pkgname=dotdrop
pkgname="${_pkgname}-git"
pkgver=0.10.r10.gafe0c71
pkgrel=1
pkgdesc="Save your dotfiles once, deploy them everywhere "
arch=('any')
url="https://github.com/deadc0de6/dotdrop"
license=('GPL')
groups=()
depends=('python' 'python-setuptools' 'python-jinja' 'python-docopt' 'python-ruamel-yaml')
makedepends=('git')
provides=(dotdrop)
conflicts=(dotdrop)
source=("git+https://github.com/deadc0de6/dotdrop.git")
md5sums=('SKIP')

pkgver() {
  cd "${_pkgname}"
  git describe --long --tags | sed 's/\([^-]*-g\)/r\1/;s/-/./g;s/^v//g'
}

package() {
  cd "${_pkgname}"
  python setup.py install --root="${pkgdir}/" --optimize=1
}

