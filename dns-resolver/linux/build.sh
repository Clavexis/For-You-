#!/usr/bin/env bash
# Build the DNS resolver on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
gcc -O2 -Wall -o dns dns.c
echo "Built ./dns — try: ./dns example.com MX"
