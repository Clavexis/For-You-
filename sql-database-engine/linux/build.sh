#!/usr/bin/env bash
# Build the SQL engine on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
gcc -O2 -o db db.c
echo "Built ./db — try: ./db mydata"
