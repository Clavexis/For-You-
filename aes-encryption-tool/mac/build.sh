#!/usr/bin/env bash
# Build the AES tool on macOS. Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
clang++ -O2 -std=c++17 -Wall -o aes aes.cpp
echo "Built ./aes — verify with: ./aes --test"
