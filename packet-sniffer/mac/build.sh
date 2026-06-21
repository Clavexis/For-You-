#!/usr/bin/env bash
# Build the packet sniffer on macOS. Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
clang -O2 -Wall -Wextra -o sniffer sniffer.c
echo "Built ./sniffer — run with: sudo ./sniffer en0  (BPF needs root)"
