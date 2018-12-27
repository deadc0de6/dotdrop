# Maintainer: deadc0de6 <info@deadc0de.ch>

pkgname=dotdrop
pkgver=0.24.1
pkgrel=1
pkgdesc="Save your dotfiles once, deploy them everywhere "
arch=('any')
url="https://github.com/deadc0de6/dotdrop"
license=('GPL')
groups=()
depends=('python' 'python-setuptools' 'python-jinja' 'python-docopt' 'python-pyaml')
makedepends=('git')
source=("git+https://github.com/deadc0de6/dotdrop.git#tag=v${pkgver}")
md5sums=('SKIP')

pkgver() {
  cd "${pkgname}"
  git describe --abbrev=0 --tags | sed 's/^v//g'
}

package() {
  cd "${pkgname}"
  python setup.py install --root="${pkgdir}/" --optimize=1
}

