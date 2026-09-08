"""Keep the browser validator and the canonical Pydantic contracts aligned."""

from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from storyboard_studio.schemas import PresentationPayload, StoryDocumentV2

ROOT = Path(__file__).resolve().parents[1]
VALIDATION_JS = ROOT / "storyboard_studio" / "web" / "static" / "validation.js"
TOKENS_JSON = ROOT / "themes" / "storyboard-tokens.json"
BLOCK_CHOICES = [
    "standard",
    "comparison",
    "decision",
    "timeline",
    "metric",
    "process",
    "quote",
    "table",
    "chart",
    "image",
]


NODE_RUNNER = r"""
const fs = require("fs");
const vm = require("vm");

const cases = JSON.parse(fs.readFileSync(0, "utf8"));
const source = fs.readFileSync(process.env.STORYBOARD_VALIDATION_JS, "utf8")
  + "\nglobalThis.__storyboardValidation = StoryboardValidation;";
const context = { console, URL, Set };
vm.createContext(context);
vm.runInContext(source, context, { filename: "validation.js" });
const themes = JSON.parse(fs.readFileSync(process.env.STORYBOARD_TOKENS_JSON, "utf8")).themes;
const choices = JSON.parse(process.env.STORYBOARD_BLOCK_CHOICES).map((value) => [value, value]);
context.__storyboardValidation.configure({ themes: () => themes, blockChoices: () => choices });

const results = cases.map((entry) => {
  const method = entry.kind === "story" ? "validateStory" : "validateOutline";
  try {
    context.__storyboardValidation[method](JSON.parse(JSON.stringify(entry.value)));
    return true;
  } catch (error) {
    return false;
  }
});
process.stdout.write(JSON.stringify(results));
"""


def _load(relative_path: str) -> dict[str, Any]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def _python_accepts(kind: str, value: dict[str, Any]) -> bool:
    model = StoryDocumentV2 if kind == "story" else PresentationPayload
    try:
        model.model_validate(value)
    except ValueError:
        return False
    return True


def _cases() -> list[dict[str, Any]]:
    product = _load("examples/product-brief.json")
    semantic = _load("examples/fixtures/semantic-blocks.json")
    evidence = _load("examples/fixtures/evidence-edge-cases.json")
    native_visuals = _load("assets/demo/native-visuals.json")
    story = _load("storyboard_studio/data/decision-brief.story.json")
    cases = [
        {"name": "product outline", "kind": "outline", "value": product},
        {"name": "semantic blocks", "kind": "outline", "value": semantic},
        {"name": "evidence edge cases", "kind": "outline", "value": evidence},
        {"name": "native visuals", "kind": "outline", "value": native_visuals},
        {"name": "decision story", "kind": "story", "value": story},
    ]

    missing_number = copy.deepcopy(product)
    del missing_number["slides"][0]["slide_number"]
    cases.append({"name": "missing slide number", "kind": "outline", "value": missing_number})

    duplicate_number = copy.deepcopy(product)
    duplicate_number["slides"][1]["slide_number"] = 1
    cases.append({"name": "non-sequential slide numbers", "kind": "outline", "value": duplicate_number})

    private_ipv6 = copy.deepcopy(evidence)
    private_ipv6["slides"][0]["sources"][0]["url"] = "http://[::1]/private"
    cases.append({"name": "private IPv6 evidence URL", "kind": "outline", "value": private_ipv6})

    backslash_asset = copy.deepcopy(native_visuals)
    backslash_asset["assets"][0]["path"] = "data\\pilot-results.csv"
    cases.append({"name": "backslash asset path", "kind": "outline", "value": backslash_asset})

    mismatched_asset = copy.deepcopy(native_visuals)
    mismatched_asset["assets"][0]["media_type"] = "image/png"
    cases.append({"name": "data asset with image media type", "kind": "outline", "value": mismatched_asset})

    unicode_claim_id = copy.deepcopy(evidence)
    unicode_claim_id["slides"][0]["sources"][0]["claim_ids"] = ["résumé"]
    cases.append({"name": "non-ascii claim id", "kind": "outline", "value": unicode_claim_id})

    long_local_reference = copy.deepcopy(evidence)
    long_local_reference["slides"][2]["sources"][0]["local_reference"] = "notes/" + ("x" * 240)
    cases.append({"name": "oversized local reference", "kind": "outline", "value": long_local_reference})

    missing_brief = copy.deepcopy(story)
    missing_brief["decision_brief"] = None
    cases.append({"name": "decision story without brief", "kind": "story", "value": missing_brief})

    wrong_template = copy.deepcopy(story)
    wrong_template["template"] = "freeform"
    cases.append({"name": "story template mismatch", "kind": "story", "value": wrong_template})
    return cases


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required for browser contract parity")
def test_browser_and_python_contracts_agree_on_curated_corpus() -> None:
    cases = _cases()
    expected = [_python_accepts(case["kind"], case["value"]) for case in cases]
    result = subprocess.run(
        ["node", "-e", NODE_RUNNER],
        cwd=ROOT,
        env={
            **os.environ,
            "STORYBOARD_VALIDATION_JS": str(VALIDATION_JS),
            "STORYBOARD_TOKENS_JSON": str(TOKENS_JSON),
            "STORYBOARD_BLOCK_CHOICES": json.dumps(BLOCK_CHOICES),
        },
        input=json.dumps(cases),
        text=True,
        capture_output=True,
        check=False,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    actual = json.loads(result.stdout)
    assert actual == expected, "browser/Python contract mismatch: " + ", ".join(
        f"{case['name']} expected={want} actual={got}"
        for case, want, got in zip(cases, expected, actual, strict=True)
        if want != got
    )
