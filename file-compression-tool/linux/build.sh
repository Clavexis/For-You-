#!/usr/bin/env bash
# Build the compression tool on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
g++ -O2 -std=c++17 -Wall -o huff huffman.cpp
echo "Built ./huff — try: ./huff -c file.txt file.huf"
