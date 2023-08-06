# Maintainer: deadc0de6 <info@deadc0de.ch>

_pkgname=dotdrop
pkgname="${_pkgname}-git"
pkgver=1.3.7.r13.g18b156e
pkgrel=8
pkgdesc="Save your dotfiles once, deploy them everywhere "
arch=('any')
url="https://github.com/deadc0de6/dotdrop"
license=('GPL')
groups=()
depends=('python' 'python-setuptools' 'python-jinja' 'python-docopt' 'python-ruamel-yaml' 'python-magic' 'python-requests' 'python-packaging' 'python-tomli-w' 'python-distro')
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
  install -Dm644 ${srcdir}/${_pkgname}/completion/_dotdrop-completion.zsh "${pkgdir}/usr/share/zsh/site-functions/_${_pkgname}"
  install -Dm644 ${srcdir}/${_pkgname}/completion/dotdrop.fish "${pkgdir}/usr/share/fish/completions/${_pkgname}.fish"
  install -Dm644 ${srcdir}/${_pkgname}/LICENSE "${pkgdir}/usr/share/licenses/${_pkgname}/LICENSE"
  install -Dm644 ${srcdir}/${_pkgname}/README.md "${pkgdir}/usr/share/doc/${_pkgname}/README.md"
}

