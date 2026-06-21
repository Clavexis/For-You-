#!/usr/bin/env bash
# Install clawtorrent on macOS (Apple Silicon & Intel). Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "${HOME}/.local/bin"
install -m 0755 "${SCRIPT_DIR}/clawtorrent.py" "${HOME}/.local/bin/clawtorrent"
echo "Installed (pure Python 3, no dependencies)."
echo "Ensure ~/.local/bin is on your PATH, then try:  clawtorrent test"
