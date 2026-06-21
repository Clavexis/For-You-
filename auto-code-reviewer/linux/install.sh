#!/usr/bin/env bash
# Install Auto Code Reviewer on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${HOME}/.local/bin"
python3 -m pip install --user -r "${SCRIPT_DIR}/requirements.txt"
mkdir -p "${BIN_DIR}"
install -m 0755 "${SCRIPT_DIR}/review.py" "${BIN_DIR}/code-review"
echo ">> Installed. Set ANTHROPIC_API_KEY, then:  code-review yourfile.py"
