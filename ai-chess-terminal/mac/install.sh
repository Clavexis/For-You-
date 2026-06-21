#!/usr/bin/env bash
# Install AI Chess (terminal) on macOS. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "${HOME}/.local/bin"
install -m 0755 "${SCRIPT_DIR}/chess.py" "${HOME}/.local/bin/ai-chess"
echo "Installed. Run:  ai-chess          (no dependencies — pure Python 3)"
