#!/usr/bin/env bash
# Install AI Dungeon on macOS. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m pip install --user -r "${SCRIPT_DIR}/requirements.txt" || true
mkdir -p "${HOME}/.local/bin"
install -m 0755 "${SCRIPT_DIR}/dungeon.py" "${HOME}/.local/bin/ai-dungeon"
echo "Installed. Play with:  ai-dungeon   (set ANTHROPIC_API_KEY for AI narration)"
