pkgname=biotools-cli
pkgver=0.1.0
pkgrel=1
pkgdesc='Read-only command line client for the bio.tools API'
arch=('any')
url='https://github.com/decent-tools-for-thought/biotools-cli'
license=('MIT')
depends=('python')
makedepends=('python-build' 'python-installer' 'python-setuptools')
checkdepends=('python-pytest')
source=()
sha256sums=()

build() {
  cd "$startdir"
  rm -rf "$srcdir/dist"
  python -m build --wheel --no-isolation --outdir "$srcdir/dist"
}

check() {
  cd "$startdir"
  PYTHONPATH=src pytest
}

package() {
  cd "$startdir"
  python -m installer --destdir="$pkgdir" "$srcdir"/dist/*.whl
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
  install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
}
