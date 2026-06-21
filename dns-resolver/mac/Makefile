# DNS Resolver — macOS. Built by clavexis — github.com/clavexis
CC ?= clang
CFLAGS ?= -O2 -Wall
.PHONY: all run clean
all: dns
dns: dns.c
	$(CC) $(CFLAGS) -o dns dns.c
run: dns
	./dns example.com
clean:
	rm -f dns
