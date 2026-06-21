#!/usr/bin/env bash
# Build the AES tool on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
g++ -O2 -std=c++17 -Wall -o aes aes.cpp
echo "Built ./aes — verify with: ./aes --test"
