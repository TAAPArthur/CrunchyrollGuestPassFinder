# Maintainer: Arthur Williams <taaparthur@gmail.com>


pkgname='taapcrunchyroll-bot'
pkgver='1.0.0'
_language='en-US'
pkgrel=1
pkgdesc='Automatically get Crunchyroll guest passes for free'

arch=('any')
license=('MIT')
depends=('python3' 'python-selenium' 'phantomjs')
md5sums=('SKIP')

install=$pkgname.install
source=("https://github.com/TAAPArthur/TAAPCrunchyrollBot/archive/master.zip")
_srcDir="TAAPCrunchyrollBot-master"

package() {
ls -l *

  mkdir "$pkgdir/usr/lib/$pkgname"
  mv "$_srcDir"/taapcrunchyroll-bot.sh "$pkgdir/usr/bin/"
  mv "$_srcDir"/*.py "$pkgdir/usr/lib/$pkgname/"
}
