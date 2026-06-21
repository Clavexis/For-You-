#!/usr/bin/env bash
# Build the ray tracer on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
g++ -O2 -std=c++17 -Wall -o raytracer raytracer.cpp
echo "Built ./raytracer — try: ./raytracer -o render.png --samples 3"
