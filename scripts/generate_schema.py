"""Write the versioned public JSON Schema for validated presentation payloads."""

from __future__ import annotations

import json
from pathlib import Path

from schemas import (
    DecisionBriefV2,
    ExportPresentationRequest,
    GenerateContentRequest,
    GuidedDecisionRequest,
    PresentationPayload,
    StoryDocumentV2,
)
from server import app

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "docs" / "schema"
PACKAGE_DATA_DIR = ROOT / "storyboard_studio" / "data"


def write_content(filename: str, value: object) -> None:
    content = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    for directory in (SCHEMA_DIR, PACKAGE_DATA_DIR):
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / filename
        destination.write_text(content, encoding="utf-8")
        print(f"Wrote {destination}")


def write_schema(model: type, filename: str, schema_id: str, title: str) -> None:
    schema = model.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = schema_id
    schema["title"] = title
    write_content(filename, schema)


def write_openapi() -> None:
    presentation = PresentationPayload.model_validate_json(
        (ROOT / "examples" / "product-brief.json").read_text(encoding="utf-8")
    )
    brief = DecisionBriefV2.model_validate_json(
        (ROOT / "examples" / "briefs" / "onboarding-decision.json").read_text(encoding="utf-8")
    )
    examples = {
        "/api/v1/content": {
            "local-no-key": GenerateContentRequest(
                topic="Choose a reliable onboarding direction",
                slide_count=3,
                brief="Align product and customer-success leaders",
                use_ai=False,
                provider="local",
            ).model_dump(mode="json")
        },
        "/api/v1/stories/decision-brief": {
            "guided-decision": GuidedDecisionRequest(brief=brief, theme="midnight").model_dump(mode="json")
        },
        "/api/v1/presentations": {
            "reviewed-presentation": ExportPresentationRequest(presentation=presentation).model_dump(
                mode="json"
            )
        },
    }
    schema = app.openapi()
    schema["info"]["x-storyboard-contract"] = {
        "schema": "storyboard-v1",
        "story_schema": "story-v2",
        "compatibility": "docs/SUPPORT_MATRIX.md",
        "migrations": "docs/MIGRATIONS.md",
    }
    for route, named_examples in examples.items():
        content = schema["paths"][route]["post"]["requestBody"]["content"]["application/json"]
        content["examples"] = {
            name: {"summary": name.replace("-", " ").title(), "value": value}
            for name, value in named_examples.items()
        }
    write_content("openapi-v1.json", schema)


def main() -> int:
    write_schema(
        ExportPresentationRequest,
        "storyboard-v1.json",
        "https://othmaneblial.github.io/Storyboard-Studio/schema/storyboard-v1.json",
        "Storyboard Studio export request v1",
    )
    write_schema(
        StoryDocumentV2,
        "story-v2.json",
        "https://othmaneblial.github.io/Storyboard-Studio/schema/story-v2.json",
        "Storyboard Studio story document v2",
    )
    write_openapi()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
