# Maintainer: deadc0de6 <info@deadc0de.ch>

_pkgname=dotdrop
pkgname="${_pkgname}-git"
pkgver=0.31.0.r7.gd860c07
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
  install -Dm644 ${srcdir}/${_pkgname}/completion/dotdrop-completion.bash "${pkgdir}/usr/share/bash-completion/completions/${_pkgname}"
  install -Dm644 ${srcdir}/${_pkgname}/completion/_dotdrop-completion.zsh "${pkgdir}/usr/share/zsh/site-functions/${_pkgname}"
}

