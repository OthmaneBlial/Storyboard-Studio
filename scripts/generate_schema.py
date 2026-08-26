"""Write the versioned public JSON Schema for validated presentation payloads."""

from __future__ import annotations

import json
from pathlib import Path

from schemas import ExportPresentationRequest

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "docs" / "schema" / "storyboard-v1.json"


def main() -> int:
    schema = ExportPresentationRequest.model_json_schema()
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://othmaneblial.github.io/Storyboard-Studio/schema/storyboard-v1.json"
    schema["title"] = "Storyboard Studio export request v1"
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {DESTINATION}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
