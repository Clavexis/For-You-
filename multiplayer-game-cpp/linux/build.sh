#!/usr/bin/env bash
# Build the multiplayer game on Linux. Built by clavexis — github.com/clavexis
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
g++ -O2 -std=c++17 -Wall -o server server.cpp
echo "Built ./server"
if pkg-config --exists sdl2; then
  g++ -O2 -std=c++17 -Wall -o client client.cpp $(pkg-config --cflags --libs sdl2)
  echo "Built ./client"
else
  echo "SDL2 not found — install it to build the client:  sudo apt install libsdl2-dev"
fi
