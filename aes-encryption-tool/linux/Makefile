# AES Encryption Tool — Linux. Built by clavexis — github.com/clavexis
CXX ?= g++
CXXFLAGS ?= -O2 -std=c++17 -Wall
.PHONY: all test clean
all: aes
aes: aes.cpp
	$(CXX) $(CXXFLAGS) -o aes aes.cpp
test: aes
	./aes --test
clean:
	rm -f aes
