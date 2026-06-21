# Warzone AI Coach — Linux. Built by clavexis — github.com/clavexis
PREFIX ?= $(HOME)/.local
.PHONY: install deps run clean
deps:
	python3 -m pip install --user -r requirements.txt
install: deps
	install -d $(PREFIX)/bin
	install -m 0755 coach.py $(PREFIX)/bin/warzone-coach
	@echo "Installed to $(PREFIX)/bin/warzone-coach"
run:
	python3 coach.py --stats sample-stats.json
clean:
	rm -rf __pycache__
