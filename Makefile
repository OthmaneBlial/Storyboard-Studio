PYTHON ?= .venv/bin/python

.PHONY: setup run test lint format-check export-sample smoke schema render-reference markdown-roundtrip

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

smoke:
	$(PYTHON) scripts/smoke.py

schema:
	$(PYTHON) scripts/generate_schema.py

render-reference:
	$(PYTHON) scripts/render_slides.py docs/fixtures/product-brief.pptx --output rendered-slides --require

markdown-roundtrip:
	$(PYTHON) scripts/outline_markdown.py --input examples/templates/decision-brief.json --output /tmp/storyboard-decision.md
	$(PYTHON) scripts/outline_markdown.py --from-markdown --input /tmp/storyboard-decision.md --output /tmp/storyboard-decision-roundtrip.json
