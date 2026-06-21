#!/usr/bin/env bash
# Build & install Claw on macOS. Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
clang++ -O2 -std=c++17 -Wall -o "${SCRIPT_DIR}/claw" "${SCRIPT_DIR}/claw.cpp"
mkdir -p "${HOME}/.local/bin"
install -m 0755 "${SCRIPT_DIR}/claw" "${HOME}/.local/bin/claw"
echo "Installed to ~/.local/bin/claw"
