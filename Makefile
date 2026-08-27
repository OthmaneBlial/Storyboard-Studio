PYTHON ?= .venv/bin/python

.PHONY: setup browser-setup browser-test run test lint format-check export-sample export-native-visuals export-evidence-fixture refresh-demo smoke schema render-reference render-semantic-fixtures markdown-roundtrip validate-assets validate-layout

setup:
	python3 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

browser-setup:
	$(PYTHON) -m pip install -e ".[dev,browser]"
	$(PYTHON) -m playwright install chromium

browser-test:
	$(PYTHON) -m pytest -q browser_tests

run:
	$(PYTHON) -m storyboard_studio.cli serve --reload

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check .

format-check:
	$(PYTHON) -m ruff format --check .

export-sample:
	$(PYTHON) -m storyboard_studio.cli export --input examples/product-brief.json --output output/product-brief.pptx

export-native-visuals:
	$(PYTHON) -m storyboard_studio.cli export --input assets/demo/native-visuals.json --output output/native-visuals.pptx

export-evidence-fixture:
	$(PYTHON) -m storyboard_studio.cli export --input examples/fixtures/evidence-edge-cases.json --output output/evidence-edge-cases.pptx --citations

refresh-demo:
	$(PYTHON) -m storyboard_studio.cli compile --input examples/briefs/onboarding-decision.json --output storyboard_studio/data/decision-brief.story.json

smoke:
	$(PYTHON) scripts/smoke.py

schema:
	$(PYTHON) scripts/generate_schema.py

render-reference:
	$(PYTHON) scripts/render_slides.py docs/fixtures/product-brief.pptx --output rendered-slides --require

render-semantic-fixtures:
	$(PYTHON) scripts/generate_semantic_fixtures.py

markdown-roundtrip:
	$(PYTHON) scripts/outline_markdown.py --input examples/templates/decision-brief.json --output /tmp/storyboard-decision.md
	$(PYTHON) scripts/outline_markdown.py --from-markdown --input /tmp/storyboard-decision.md --output /tmp/storyboard-decision-roundtrip.json

validate-assets:
	$(PYTHON) scripts/validate_assets.py

validate-layout:
	$(PYTHON) scripts/validate_layout.py
