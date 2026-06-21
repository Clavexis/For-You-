#!/usr/bin/env bash
# Build and install the chess engine on macOS (Apple Silicon & Intel). Built by clavexis — github.com/clavexis
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
clang++ -O2 -std=c++17 -Wall -o "${SCRIPT_DIR}/chess" "${SCRIPT_DIR}/chess.cpp"
mkdir -p "${HOME}/.local/bin"
install -m 0755 "${SCRIPT_DIR}/chess" "${HOME}/.local/bin/chess-engine"
echo "Installed to ~/.local/bin/chess-engine"
