#!/usr/bin/env bash
# Install Warzone AI Coach on macOS (Apple Silicon & Intel).
# Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
command -v python3 >/dev/null 2>&1 || { echo "Install Python: brew install python"; exit 1; }
echo ">> Installing dependencies (anthropic SDK optional, enables AI coaching)..."
python3 -m pip install --user -r "${SCRIPT_DIR}/requirements.txt"
mkdir -p "${BIN_DIR}"
install -m 0755 "${SCRIPT_DIR}/coach.py" "${BIN_DIR}/warzone-coach"
echo ">> Done. Try:  warzone-coach --stats ${SCRIPT_DIR}/sample-stats.json"
