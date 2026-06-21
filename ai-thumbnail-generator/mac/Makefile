# AI Thumbnail Generator — Linux. Built by clavexis — github.com/clavexis
PREFIX ?= $(HOME)/.local
.PHONY: install deps run clean
deps:
	python3 -m pip install --user -r requirements.txt
install: deps
	install -d $(PREFIX)/bin
	install -m 0755 thumbnail.py $(PREFIX)/bin/thumbgen
run:
	python3 thumbnail.py "Sample Thumbnail" --style tech
clean:
	rm -rf __pycache__ thumbnails
