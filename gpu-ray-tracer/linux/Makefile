# Ray Tracer — Linux. Built by clavexis — github.com/clavexis
CXX ?= g++
CXXFLAGS ?= -O2 -std=c++17 -Wall
.PHONY: all run clean
all: raytracer
raytracer: raytracer.cpp
	$(CXX) $(CXXFLAGS) -o raytracer raytracer.cpp
run: raytracer
	./raytracer -o render.png --width 800 --height 600 --samples 3
clean:
	rm -f raytracer render.png
