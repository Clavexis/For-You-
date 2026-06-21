#!/usr/bin/env bash
# Install Local AI Autocomplete on macOS. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "1) Install Ollama:  brew install ollama   (or download from ollama.com)"
echo "2) Pull a code model:  ollama pull qwen2.5-coder:1.5b"
echo "3) Run the bridge:  python3 ${SCRIPT_DIR}/server.py"
echo "4) Install the VS Code extension from ${SCRIPT_DIR}/extension (see README)."
