# File Compression Tool — macOS. Built by clavexis — github.com/clavexis
CXX ?= clang++
CXXFLAGS ?= -O2 -std=c++17 -Wall
.PHONY: all clean
all: huff
huff: huffman.cpp
	$(CXX) $(CXXFLAGS) -o huff huffman.cpp
clean:
	rm -f huff
