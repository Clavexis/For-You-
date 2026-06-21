#!/usr/bin/env bash
# Install Real-Time Code Collab on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m pip install --user -r "${SCRIPT_DIR}/requirements.txt"
mkdir -p "${HOME}/.local/bin"
install -m 0755 "${SCRIPT_DIR}/collab.py" "${HOME}/.local/bin/collab"
echo "Installed. Start a server:  collab server   then:  collab join myroom"
