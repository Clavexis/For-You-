#!/usr/bin/env bash
# Install the AI Terminal Assistant on macOS (Apple Silicon or Intel).
# Built by clavexis — github.com/clavexis
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"

# Ensure a Python 3 is available; nudge toward Homebrew if not.
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found. Install it with Homebrew:  brew install python"
  exit 1
fi

echo ">> Installing Python dependencies..."
python3 -m pip install --user -r "${SCRIPT_DIR}/requirements.txt"

echo ">> Linking 'ai-assistant' into ${BIN_DIR}..."
mkdir -p "${BIN_DIR}"
install -m 0755 "${SCRIPT_DIR}/assistant.py" "${BIN_DIR}/ai-assistant"

echo ">> Done."
echo "   Add ${BIN_DIR} to your PATH (zsh):"
echo "     echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.zshrc"
echo "   Then run:  ai-assistant --set-key sk-ant-...   &&   ai-assistant"
