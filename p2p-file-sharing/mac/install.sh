#!/usr/bin/env bash
# Install P2P File Sharing on macOS. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m pip install --user -r "${SCRIPT_DIR}/requirements.txt"
mkdir -p "${HOME}/.local/bin"
install -m 0755 "${SCRIPT_DIR}/p2p.py" "${HOME}/.local/bin/p2p"
echo "Installed. Send:  p2p send file.zip   |   Receive:  p2p recv HOST PORT CODE"
