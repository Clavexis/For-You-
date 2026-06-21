# HTTP Server — Linux. Built by clavexis — github.com/clavexis
CXX ?= g++
CXXFLAGS ?= -O2 -std=c++17 -Wall -pthread
.PHONY: all run clean
all: server
server: server.cpp
	$(CXX) $(CXXFLAGS) -o server server.cpp
run: server
	./server --port 8080 --root ../www
clean:
	rm -f server
