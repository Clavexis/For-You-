#!/usr/bin/env bash
# Install Keylogger Detector on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "${HOME}/.local/bin"
install -m 0755 "${SCRIPT_DIR}/detector.py" "${HOME}/.local/bin/keylogger-detector"
echo "Installed. Run:  keylogger-detector   (pure Python, no dependencies)"
