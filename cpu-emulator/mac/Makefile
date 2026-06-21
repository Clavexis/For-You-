# CHIP-8 Emulator — macOS. Built by clavexis — github.com/clavexis
CXX ?= clang++
CXXFLAGS ?= -O2 -std=c++17 -Wall
.PHONY: all test clean
all: chip8
chip8: chip8.cpp main.cpp chip8.h
	$(CXX) $(CXXFLAGS) -o chip8 chip8.cpp main.cpp
test: chip8
	./chip8 --test
clean:
	rm -f chip8
