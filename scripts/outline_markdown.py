"""Convert a validated Storyboard JSON outline to/from deterministic Markdown."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from outline_markdown import markdown_to_presentation, presentation_to_markdown
from schemas import PresentationPayload


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert Storyboard outlines and Markdown")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--from-markdown", action="store_true")
    args = parser.parse_args()
    raw = args.input.read_text(encoding="utf-8")
    if args.from_markdown:
        data = PresentationPayload.model_validate(markdown_to_presentation(raw)).model_dump()
        args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    else:
        data = PresentationPayload.model_validate(json.loads(raw)).model_dump()
        args.output.write_text(presentation_to_markdown(data), encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
