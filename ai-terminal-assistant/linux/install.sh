#!/usr/bin/env bash
# Install the AI Terminal Assistant on Linux (Debian/Ubuntu/Arch).
# Built by clavexis — github.com/clavexis
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"

echo ">> Installing Python dependencies..."
python3 -m pip install --user -r "${SCRIPT_DIR}/requirements.txt"

echo ">> Linking 'ai-assistant' into ${BIN_DIR}..."
mkdir -p "${BIN_DIR}"
install -m 0755 "${SCRIPT_DIR}/assistant.py" "${BIN_DIR}/ai-assistant"

echo ">> Done."
echo "   Make sure ${BIN_DIR} is on your PATH, then run:"
echo "   ai-assistant --set-key sk-ant-...   # store your key once"
echo "   ai-assistant                        # start chatting"
