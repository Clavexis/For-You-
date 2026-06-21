# SQL Database Engine — Linux. Built by clavexis — github.com/clavexis
CC ?= gcc
CFLAGS ?= -O2 -Wall
.PHONY: all run clean
all: db
db: db.c
	$(CC) $(CFLAGS) -o db db.c
run: db
	./db mydata
clean:
	rm -f db
