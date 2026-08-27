PYTHON ?= .venv/bin/python

.PHONY: setup browser-setup browser-test run test lint format-check export-sample export-native-visuals export-evidence-fixture refresh-demo smoke schema schema-check render-reference render-semantic-fixtures markdown-roundtrip review-story tool-contract benchmark benchmark-check benchmark-fixture-check validate-contribution validate-assets validate-layout

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

schema-check: schema
	git diff --exit-code -- docs/schema/storyboard-v1.json docs/schema/story-v2.json docs/schema/openapi-v1.json storyboard_studio/data/storyboard-v1.json storyboard_studio/data/story-v2.json storyboard_studio/data/openapi-v1.json

render-reference:
	$(PYTHON) scripts/render_slides.py docs/fixtures/product-brief.pptx --output rendered-slides --require

render-semantic-fixtures:
	$(PYTHON) scripts/generate_semantic_fixtures.py

markdown-roundtrip:
	$(PYTHON) -m storyboard_studio.cli export --input storyboard_studio/data/decision-brief.story.json --output /tmp/storyboard-decision.story.md --format markdown
	$(PYTHON) -m storyboard_studio.cli import /tmp/storyboard-decision.story.md --output /tmp/storyboard-decision-roundtrip.story.json
	$(PYTHON) -m storyboard_studio.cli export --input /tmp/storyboard-decision.story.md --output /tmp/storyboard-decision-roundtrip.pptx --format pptx

review-story:
	$(PYTHON) scripts/review_story.py --input storyboard_studio/data/decision-brief.story.json --output-dir output/review-action --repository .

tool-contract:
	bash -n examples/integrations/local_cli.sh
	$(PYTHON) -m py_compile examples/integrations/http_api.py examples/integrations/tool_client.py
	$(PYTHON) -c 'import json, subprocess; request=json.dumps({"id":"ci","action":"capabilities","arguments":{}})+"\n"; result=subprocess.run(["$(PYTHON)","-m","storyboard_studio.cli","tools","--workspace",".","--output-dir","output/tool-check","--once"],input=request,text=True,capture_output=True,check=True); response=json.loads(result.stdout); assert response["ok"] and response["result"]["network"] == "none"'

benchmark:
	$(PYTHON) -m storyboard_studio.cli benchmark --suite benchmarks/decision-v1/suite.json --output-dir output/benchmark --release local-check --overwrite

benchmark-check:
	$(PYTHON) -m storyboard_studio.cli benchmark --suite benchmarks/decision-v1/suite.json --output-dir output/benchmark-check --release current-source --baseline benchmarks/decision-v1/baseline/main-2026-08-27/report.json --overwrite --fail-on-regression

benchmark-fixture-check:
	cmp benchmarks/decision-v1/suite.json storyboard_studio/data/decision-benchmark-v1.json

validate-contribution:
	$(PYTHON) -m storyboard_studio.cli validate-contribution examples/templates/decision-brief.contribution.json --output-dir output/contribution-validation --overwrite

validate-assets:
	$(PYTHON) scripts/validate_assets.py

validate-layout:
	$(PYTHON) scripts/validate_layout.py
