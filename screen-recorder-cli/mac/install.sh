#!/usr/bin/env bash
# Install Screen Recorder CLI on macOS. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
command -v ffmpeg >/dev/null || echo "Note: install ffmpeg first:  brew install ffmpeg"
mkdir -p "${HOME}/.local/bin"
install -m 0755 "${SCRIPT_DIR}/screenrec.py" "${HOME}/.local/bin/screenrec"
echo "Installed. Record:  screenrec out.mp4 --duration 10"
echo "(Grant Screen Recording permission to your terminal in System Settings > Privacy.)"
