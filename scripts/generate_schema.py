"""Write the versioned public JSON Schema for validated presentation payloads."""

from __future__ import annotations

import json
from pathlib import Path

from schemas import ExportPresentationRequest, StoryDocumentV2

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "docs" / "schema"
PACKAGE_DATA_DIR = ROOT / "storyboard_studio" / "data"


def write_schema(model: type, filename: str, schema_id: str, title: str) -> None:
    schema = model.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = schema_id
    schema["title"] = title
    content = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"
    for directory in (SCHEMA_DIR, PACKAGE_DATA_DIR):
        directory.mkdir(parents=True, exist_ok=True)
        destination = directory / filename
        destination.write_text(content, encoding="utf-8")
        print(f"Wrote {destination}")


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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
