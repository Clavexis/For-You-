#!/usr/bin/env bash
# Install Discord AI Bot on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 -m pip install --user -r "${SCRIPT_DIR}/requirements.txt"
echo ">> Installed. Copy config.json.example to config.json and add your tokens,"
echo "   then run:  python3 ${SCRIPT_DIR}/bot.py"
