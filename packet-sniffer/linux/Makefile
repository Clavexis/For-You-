# Packet Sniffer — Linux. Built by clavexis — github.com/clavexis
CC ?= gcc
CFLAGS ?= -O2 -Wall -Wextra
.PHONY: all run clean
all: sniffer
sniffer: sniffer.c
	$(CC) $(CFLAGS) -o sniffer sniffer.c
run: sniffer
	sudo ./sniffer
clean:
	rm -f sniffer
