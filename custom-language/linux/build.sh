#!/usr/bin/env bash
# Build the Claw interpreter on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
g++ -O2 -std=c++17 -Wall -o claw claw.cpp
echo "Built ./claw — try:  ./claw ../examples/fizzbuzz.claw"
