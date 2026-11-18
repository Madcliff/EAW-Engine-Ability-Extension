#!/bin/sh
# Linux / Steam Deck launcher for the ZZ_SWFOC engine patch installer (needs python3, which every distro ships).
#   ./install.sh                 install
#   ./install.sh uninstall       remove
#   ./install.sh status          show what is installed
#   ./install.sh --game-dir "/path/to/Star Wars Empire at War"
cd "$(dirname "$0")" || exit 1
if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is needed: install it with your package manager (e.g. sudo apt install python3)" >&2
    exit 1
fi
exec python3 -I ./install.py "$@"
