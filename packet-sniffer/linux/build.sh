#!/usr/bin/env bash
# Build the packet sniffer on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
gcc -O2 -Wall -Wextra -o sniffer sniffer.c
echo "Built ./sniffer — run with: sudo ./sniffer  (raw sockets need root)"
