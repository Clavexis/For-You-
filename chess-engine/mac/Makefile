# Chess Engine — Linux. Built by clavexis — github.com/clavexis
CXX ?= clang++
CXXFLAGS ?= -O2 -std=c++17 -Wall
.PHONY: all run perft clean
all: chess
chess: chess.cpp
	$(CXX) $(CXXFLAGS) -o chess chess.cpp
run: chess
	./chess
perft: chess
	./chess --perft 4
clean:
	rm -f chess
