PYTHON ?= .venv/bin/python

.PHONY: setup run test lint format-check export-sample

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

run:
	$(PYTHON) -m uvicorn server:app --reload

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

format-check:
	$(PYTHON) -m ruff format --check .

export-sample:
	$(PYTHON) generate_pptx.py --input examples/product-brief.json --output output/product-brief.pptx
