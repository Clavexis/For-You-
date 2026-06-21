# Voice to Code — Linux. Built by clavexis — github.com/clavexis
PREFIX ?= $(HOME)/.local
.PHONY: install deps clean
deps:
	python3 -m pip install --user anthropic
install: deps
	install -d $(PREFIX)/bin
	install -m 0755 voice_to_code.py $(PREFIX)/bin/voice-to-code
	@echo "Installed to $(PREFIX)/bin/voice-to-code"
clean:
	rm -rf __pycache__
