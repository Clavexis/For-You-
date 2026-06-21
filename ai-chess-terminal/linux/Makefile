# AI Chess Terminal — Linux. Built by clavexis — github.com/clavexis
PREFIX ?= $(HOME)/.local
.PHONY: install run perft clean
install:
	install -d $(PREFIX)/bin
	install -m 0755 chess.py $(PREFIX)/bin/ai-chess
	@echo "Installed to $(PREFIX)/bin/ai-chess"
run:
	python3 chess.py
perft:
	python3 chess.py --perft 3
clean:
	rm -rf __pycache__
