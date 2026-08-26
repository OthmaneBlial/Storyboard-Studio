.PHONY: setup run test lint format-check export-sample

setup:
	python3 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -e ".[dev]"

run:
	python3 -m uvicorn server:app --reload

test:
	python3 -m pytest

lint:
	python3 -m ruff check .

format-check:
	python3 -m ruff format --check .

export-sample:
	python3 generate_pptx.py --input examples/product-brief.json --output output/product-brief.pptx
