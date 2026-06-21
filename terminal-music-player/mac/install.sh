#!/usr/bin/env bash
# Install Terminal Music Player on macOS. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m pip install --user -r "${SCRIPT_DIR}/requirements.txt"
mkdir -p "${HOME}/.local/bin"
install -m 0755 "${SCRIPT_DIR}/player.py" "${HOME}/.local/bin/spotify-cli"
echo "Installed. Set up Spotify credentials (see README), then:  spotify-cli now"
