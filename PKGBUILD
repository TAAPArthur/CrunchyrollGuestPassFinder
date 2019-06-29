# Maintainer: Arthur Williams <taaparthur@gmail.com>


pkgname='crunchyroll-guest-pass-finder'
pkgver='2.0.1'
_language='en-US'
pkgrel=0
pkgdesc='Automatically get Crunchyroll guest passes for free'

arch=('any')
license=('MIT')
depends=('python3' 'python-selenium' )
optdepends=('firefox' 'geckodriver' 'phantomjs' )
md5sums=('SKIP')

source=("git+https://github.com/TAAPArthur/CrunchyrollGuestPassFinder.git")
_srcDir="CrunchyrollGuestPassFinder"

package() {
  cd "$_srcDir"
  install -D -m 0755 "crunchyroll-guest-pass-finder.py" "$pkgdir/usr/bin/crunchyroll-guest-pass-finder"
  install -m 0744 -Dt "$pkgdir/usr/share/man/man1/" crunchyroll-guest-pass-finder.1
  install -D -m 0755 "crunchyroll-guest-pass-finder-autocomplete.sh" "$pkgdir/etc/bash_completion.d/crunchyroll-guest-pass-finder-autocomplete"

}
