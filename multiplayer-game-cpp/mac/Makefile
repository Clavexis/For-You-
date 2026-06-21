# Multiplayer Game — macOS. Built by clavexis — github.com/clavexis
CXX ?= clang++
CXXFLAGS ?= -O2 -std=c++17 -Wall
SDL := $(shell pkg-config --cflags --libs sdl2 2>/dev/null)
.PHONY: all server client clean
all: server client
server: server.cpp protocol.h
	$(CXX) $(CXXFLAGS) -o server server.cpp
client: client.cpp protocol.h
	@if [ -z "$(SDL)" ]; then echo "SDL2 not found — install libsdl2-dev to build the client."; exit 1; fi
	$(CXX) $(CXXFLAGS) -o client client.cpp $(SDL)
clean:
	rm -f server client
