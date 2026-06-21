#!/usr/bin/env bash
# Install AI Thumbnail Generator on macOS. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m pip install --user -r "${SCRIPT_DIR}/requirements.txt"
mkdir -p "${HOME}/.local/bin"
install -m 0755 "${SCRIPT_DIR}/thumbnail.py" "${HOME}/.local/bin/thumbgen"
echo "Installed. Try:  thumbgen \"My Video Title\" --style gaming"
