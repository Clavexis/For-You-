#!/usr/bin/env bash
# Build the CHIP-8 emulator on macOS (Apple Silicon & Intel). Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
clang++ -O2 -std=c++17 -Wall -o chip8 chip8.cpp main.cpp
echo "Built ./chip8 — verify with: ./chip8 --test"
