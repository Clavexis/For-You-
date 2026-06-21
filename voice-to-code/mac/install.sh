#!/usr/bin/env bash
# Install Voice to Code on macOS (Apple Silicon & Intel). Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
echo ">> Installing core dependency (anthropic)..."
python3 -m pip install --user anthropic
echo ">> (Optional) for mic recording + offline transcription run:"
echo "   pip install --user sounddevice numpy openai-whisper"
mkdir -p "${BIN_DIR}"
install -m 0755 "${SCRIPT_DIR}/voice_to_code.py" "${BIN_DIR}/voice-to-code"
echo ">> Installed. Try:  voice-to-code --text 'a CLI calculator' --lang python"
