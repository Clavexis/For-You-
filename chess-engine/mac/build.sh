#!/usr/bin/env bash
# Build the chess engine on macOS (Apple Silicon & Intel). Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
clang++ -O2 -std=c++17 -Wall -o chess chess.cpp
echo "Built ./chess — run it with ./chess  (or ./chess --depth 5)"
