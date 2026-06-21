#!/usr/bin/env bash
# Install Warzone Clip Highlighter on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
command -v ffmpeg >/dev/null || echo "Note: install ffmpeg first:  sudo apt install ffmpeg"
mkdir -p "${HOME}/.local/bin"
install -m 0755 "${SCRIPT_DIR}/highlighter.py" "${HOME}/.local/bin/wz-highlight"
echo "Installed. Try:  wz-highlight gameplay.mp4 -o highlights.mp4"
