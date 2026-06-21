#!/usr/bin/env bash
# Install clawbrowse on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "${HOME}/.local/bin"
install -m 0755 "${SCRIPT_DIR}/clawbrowse.py" "${HOME}/.local/bin/clawbrowse"
echo "Installed (pure Python 3, no dependencies). Try:  clawbrowse https://example.com"
