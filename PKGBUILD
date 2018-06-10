# Maintainer: Arthur Williams <taaparthur@gmail.com>


pkgname='taapcrunchyroll-bot'
pkgver='1.1.3'
_language='en-US'
pkgrel=5
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
  mkdir -p "$pkgdir/usr/lib/$pkgname/Examples"
  install -D -m 0755 "taapcrunchyroll-bot" "$pkgdir/usr/bin/"
  install -D -m 0755 "taapmessage" "$pkgdir/usr/bin/"
  install -D -m 0755 *.py "$pkgdir/usr/lib/$pkgname/"
  install -D -m 0755 Examples/* "$pkgdir/usr/lib/$pkgname/Examples"
  install -D -m 0755 taapcrunchyroll-config "$pkgdir/usr/lib/$pkgname/"
}
