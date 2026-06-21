# Neural Network from Scratch — macOS. Built by clavexis — github.com/clavexis
CXX ?= clang++
CXXFLAGS ?= -O3 -std=c++17 -Wall
.PHONY: all demo clean
all: neuralnet
neuralnet: neuralnet.cpp
	$(CXX) $(CXXFLAGS) -o neuralnet neuralnet.cpp
demo: neuralnet
	./neuralnet --demo
clean:
	rm -f neuralnet
