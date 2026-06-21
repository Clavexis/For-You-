#!/usr/bin/env bash
# Build the SQL engine on macOS. Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
clang -O2 -o db db.c
echo "Built ./db — try: ./db mydata"
