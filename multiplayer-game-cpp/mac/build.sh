#!/usr/bin/env bash
# Build the multiplayer game on macOS. Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
clang++ -O2 -std=c++17 -Wall -o server server.cpp
echo "Built ./server"
if pkg-config --exists sdl2; then
  clang++ -O2 -std=c++17 -Wall -o client client.cpp $(pkg-config --cflags --libs sdl2)
  echo "Built ./client"
else
  echo "SDL2 not found — install it to build the client:  brew install sdl2"
fi
