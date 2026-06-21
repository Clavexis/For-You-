#!/usr/bin/env bash
# Install AI Resume Builder on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m pip install --user -r "${SCRIPT_DIR}/requirements.txt" || true
mkdir -p "${HOME}/.local/bin"
install -m 0755 "${SCRIPT_DIR}/resume.py" "${HOME}/.local/bin/resume-builder"
echo "Installed. Try:  resume-builder --resume me.txt --job jd.txt"
