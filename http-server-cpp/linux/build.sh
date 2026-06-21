#!/usr/bin/env bash
# Build the HTTP server on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
g++ -O2 -std=c++17 -Wall -pthread -o server server.cpp
echo "Built ./server — run:  ./server --port 8080 --root ../www"
