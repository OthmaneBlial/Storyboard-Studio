import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from schemas import PresentationPayload
from storyboard_studio.semantic import block_plain_text, normalize_content_block

FIXTURE = Path("examples/fixtures/semantic-blocks.json")


def test_semantic_fixture_uses_eight_distinct_validated_contracts():
    payload = PresentationPayload.model_validate_json(FIXTURE.read_text(encoding="utf-8"))

    assert [slide.content_block.type for slide in payload.slides] == [
        "standard",
        "comparison",
        "decision",
        "timeline",
        "metric",
        "process",
        "quote",
        "table",
    ]
    assert all(slide.bullet_points == [] for slide in payload.slides)
    assert all(block_plain_text(slide.content_block.model_dump(mode="json")) for slide in payload.slides)


def test_legacy_three_point_slide_has_an_explicit_semantic_adapter():
    legacy = json.loads(Path("examples/product-brief.json").read_text(encoding="utf-8"))["slides"][0]
    block = normalize_content_block(legacy)

    assert block["type"] == legacy.get("block", "standard")
    assert block_plain_text(block)


def test_semantic_block_type_and_table_width_are_strict():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    fixture["slides"][0]["block"] = "metric"
    with pytest.raises(ValidationError, match="content_block.type"):
        PresentationPayload.model_validate(fixture)

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    fixture["slides"][-1]["content_block"]["rows"][0]["cells"] = ["Too few", "cells"]
    with pytest.raises(ValidationError, match="column count"):
        PresentationPayload.model_validate(fixture)
