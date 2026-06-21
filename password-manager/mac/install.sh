#!/usr/bin/env bash
# Install Password Manager on macOS. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m pip install --user -r "${SCRIPT_DIR}/requirements.txt"
mkdir -p "${HOME}/.local/bin"
install -m 0755 "${SCRIPT_DIR}/vault.py" "${HOME}/.local/bin/pwvault"
echo "Installed. Start with:  pwvault init"
