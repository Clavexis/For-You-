#!/usr/bin/env bash
# Build the neural network on macOS. Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
clang++ -O3 -std=c++17 -Wall -o neuralnet neuralnet.cpp
echo "Built ./neuralnet — try: ./neuralnet --demo"
