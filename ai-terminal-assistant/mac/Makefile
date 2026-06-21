# AI Terminal Assistant — macOS build/install helpers
# Built by clavexis — github.com/clavexis

PREFIX ?= $(HOME)/.local

.PHONY: install deps run clean

deps:
	python3 -m pip install --user -r requirements.txt

install: deps
	install -d $(PREFIX)/bin
	install -m 0755 assistant.py $(PREFIX)/bin/ai-assistant
	@echo "Installed to $(PREFIX)/bin/ai-assistant"

run:
	python3 assistant.py

clean:
	rm -rf __pycache__
