"""Validate the local-only asset manifest before an experimental render."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from schemas import LocalAsset
from storyboard_studio.assets import resolve_assets, validate_data_asset

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "manifest.json"


def main() -> int:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assets = payload.get("assets")
    if not isinstance(assets, list):
        raise SystemExit("assets/manifest.json must contain an assets list")
    entries = [LocalAsset.model_validate(item) for item in assets]
    with tempfile.TemporaryDirectory(prefix="storyboard-manifest-") as temporary:
        resolved = resolve_assets(entries, ROOT / "assets", Path(temporary))
        for asset in resolved.values():
            if asset.entry.kind == "data":
                validate_data_asset(asset)
    print(f"Asset manifest valid: {len(assets)} local asset(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
