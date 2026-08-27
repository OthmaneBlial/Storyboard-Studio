"""Validate the source, packaged, and example local layout contracts."""

from __future__ import annotations

import json
from pathlib import Path

from storyboard_studio.layout import load_brand_kit, load_layout_contract


def main() -> int:
    source_path = Path("themes/storyboard-tokens.json")
    packaged_path = Path("storyboard_studio/data/storyboard-tokens.json")
    source = load_layout_contract(source_path)
    packaged = load_layout_contract(packaged_path)
    if source.model_dump(mode="json") != packaged.model_dump(mode="json"):
        raise SystemExit(
            "Source and packaged layout contracts differ. Sync themes/storyboard-tokens.json "
            "with storyboard_studio/data/storyboard-tokens.json."
        )
    kit = load_brand_kit("themes/brand-kit.example.json")
    summary = {
        "layout_schema": source.schema_version,
        "themes": len(source.themes),
        "brand_kit": kit.name,
        "remote_resources": 0,
    }
    print("Layout contract valid: " + json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
