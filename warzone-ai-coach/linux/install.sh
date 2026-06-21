#!/usr/bin/env bash
# Install Warzone AI Coach on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
echo ">> Installing dependencies (anthropic SDK is optional but enables AI coaching)..."
python3 -m pip install --user -r "${SCRIPT_DIR}/requirements.txt"
mkdir -p "${BIN_DIR}"
install -m 0755 "${SCRIPT_DIR}/coach.py" "${BIN_DIR}/warzone-coach"
echo ">> Done. Try:  warzone-coach --stats ${SCRIPT_DIR}/sample-stats.json"
