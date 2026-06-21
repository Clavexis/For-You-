#!/usr/bin/env bash
# Install AI Commit Writer on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m pip install --user -r "${SCRIPT_DIR}/requirements.txt"
mkdir -p "${HOME}/.local/bin"
install -m 0755 "${SCRIPT_DIR}/aicommit.py" "${HOME}/.local/bin/aicommit"
echo "Installed. In any git repo:  git add .  &&  aicommit --commit"
