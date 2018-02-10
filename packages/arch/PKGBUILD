# Maintainer: deadc0de6 <info@deadc0de.ch>

pkgname=dotdrop
pkgver=0.10
pkgrel=1
pkgdesc="Save your dotfiles once, deploy them everywhere "
arch=('any')
url="https://github.com/deadc0de6/dotdrop"
license=('GPL')
groups=()
depends=('python' 'python-jinja' 'python-docopt' 'python-pyaml')
source=("git+https://github.com/deadc0de6/dotdrop.git")
md5sums=('SKIP')

package() {
  cd "${pkgname}"
  python setup.py install --root="${pkgdir}/"
}

