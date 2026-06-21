# Packet Sniffer — macOS. Built by clavexis — github.com/clavexis
CC ?= clang
CFLAGS ?= -O2 -Wall -Wextra
.PHONY: all run clean
all: sniffer
sniffer: sniffer.c
	$(CC) $(CFLAGS) -o sniffer sniffer.c
run: sniffer
	sudo ./sniffer en0
clean:
	rm -f sniffer
