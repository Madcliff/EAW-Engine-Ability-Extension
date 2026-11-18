#!/bin/sh
# Builds the player release zip: dist/EAW-Engine-Ability-Extension-v<version>.zip
#   release/make_release.sh <version> [--no-build]
# --no-build packages the existing dll/ZZ_SWFOC.dll instead of running dll/build.sh (which needs the stock exe).
set -e
cd "$(dirname "$0")/.."
VER="$1"
[ -n "$VER" ] || { echo "usage: $0 <version> [--no-build]" >&2; exit 1; }
[ "$2" = "--no-build" ] || dll/build.sh
NAME="EAW-Engine-Ability-Extension-v$VER"
OUT="dist/$NAME"
rm -rf "${OUT:?}" "dist/$NAME.zip"
mkdir -p "$OUT"
cp dll/ZZ_SWFOC.dll install.py install.sh LICENSE "$OUT/"
cp docs/INSTALL.md "$OUT/INSTALL.md"
cp release/Install.bat release/Uninstall.bat release/Status.bat "$OUT/"
# Windows scripts with CRLF line endings
sed 's/\r*$/\r/' install.ps1 > "$OUT/install.ps1"
chmod +x "$OUT/install.sh" "$OUT/install.py"
(cd "$OUT" && sha256sum ZZ_SWFOC.dll install.ps1 install.py install.sh Install.bat Uninstall.bat Status.bat > SHA256SUMS.txt)
(cd dist && zip -qr -X "$NAME.zip" "$NAME")
echo "wrote dist/$NAME.zip"
sha256sum "dist/$NAME.zip"
