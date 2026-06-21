#!/usr/bin/env bash
# Install mygit on macOS. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "${HOME}/.local/bin"
install -m 0755 "${SCRIPT_DIR}/mygit.py" "${HOME}/.local/bin/mygit"
echo "Installed (pure Python, no deps). Try:  mygit init"
