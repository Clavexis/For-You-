# Auto Code Reviewer — Linux. Built by clavexis — github.com/clavexis
PREFIX ?= $(HOME)/.local
.PHONY: install deps clean
deps:
	python3 -m pip install --user -r requirements.txt
install: deps
	install -d $(PREFIX)/bin
	install -m 0755 review.py $(PREFIX)/bin/code-review
	@echo "Installed to $(PREFIX)/bin/code-review"
clean:
	rm -rf __pycache__
