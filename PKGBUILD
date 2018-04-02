# Maintainer: Arthur Williams <taaparthur@gmail.com>


pkgname='taapcrunchyroll-bot'
pkgver='1.1.1'
_language='en-US'
pkgrel=1
pkgdesc='Automatically get Crunchyroll guest passes for free'

arch=('any')
license=('MIT')
depends=('python3' 'python-selenium' 'geckodriver' 'firefox')
md5sums=('SKIP')

source=("git://github.com/TAAPArthur/TAAPCrunchyrollBot.git")
_srcDir="TAAPCrunchyrollBot"

package() {

  cd "$_srcDir"
  mkdir -p "$pkgdir/usr/bin/"
  mkdir -p "$pkgdir/usr/lib/$pkgname/"
  install -D -m 0755 "taapcrunchyroll-bot" "$pkgdir/usr/bin/"
  install -D -m 0755 *.py "$pkgdir/usr/lib/$pkgname/"
}
