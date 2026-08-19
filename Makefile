.PHONY: help venv install test clean draft build publish

VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

help:
	@echo "Targets:"
	@echo "  make venv     - create virtualenv in ./venv"
	@echo "  make install  - create venv (if needed) and install requirements"
	@echo "  make test     - run pytest"
	@echo "  make draft TOPIC=\"Travel\" LEVEL=B1   - python main.py draft"
	@echo "  make build FILE=drafts/xxx.md          - python main.py build"
	@echo "  make publish FILE=drafts/xxx.md         - python main.py publish"
	@echo "  make clean    - remove caches and __pycache__"

$(PYTHON):
	python3 -m venv $(VENV)

venv: $(PYTHON)

install: venv
	$(PIP) install -r requirements.txt

test: venv
	$(PYTHON) -m pytest

draft: venv
	$(PYTHON) main.py draft "$(TOPIC)" $(LEVEL)

build: venv
	$(PYTHON) main.py build $(FILE)

publish: venv
	$(PYTHON) main.py publish $(FILE)

clean:
	find . -type d -name '__pycache__' -not -path './venv/*' -exec rm -rf {} +
	rm -rf .pytest_cache
