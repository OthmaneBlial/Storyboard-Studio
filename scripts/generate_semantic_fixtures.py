"""Generate the dark and light semantic-block PPTX fixtures from one contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from generate_pptx import create_presentation
from storyboard_studio.schemas import PresentationPayload

PUBLIC_THEMES = ("midnight", "glacier", "ember", "forest", "royal", "sakura")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("examples/fixtures/semantic-blocks.json"),
    )
    parser.add_argument("--output", type=Path, default=Path("output/semantic-blocks"))
    parser.add_argument(
        "--themes",
        nargs="+",
        choices=PUBLIC_THEMES,
        default=("midnight", "glacier"),
        help="Themes to render (defaults to the dark/light contract fixtures).",
    )
    args = parser.parse_args()

    fixture = json.loads(args.input.read_text(encoding="utf-8"))
    args.output.mkdir(parents=True, exist_ok=True)
    for theme in args.themes:
        fixture["theme"] = theme
        payload = PresentationPayload.model_validate(fixture).model_dump(mode="json")
        destination = create_presentation(
            payload,
            args.output / f"semantic-blocks-{theme}.pptx",
        )
        print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
