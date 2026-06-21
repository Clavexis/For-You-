# Claw language — Linux. Built by clavexis — github.com/clavexis
CXX ?= g++
CXXFLAGS ?= -O2 -std=c++17 -Wall
.PHONY: all run clean
all: claw
claw: claw.cpp
	$(CXX) $(CXXFLAGS) -o claw claw.cpp
run: claw
	./claw ../examples/fib.claw
clean:
	rm -f claw
