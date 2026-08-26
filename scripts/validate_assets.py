"""Validate the local-only asset manifest before an experimental render."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "assets" / "manifest.json"


def main() -> int:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assets = payload.get("assets")
    if not isinstance(assets, list):
        raise SystemExit("assets/manifest.json must contain an assets list")
    for item in assets:
        if not isinstance(item, dict):
            raise SystemExit("every asset manifest entry must be an object")
        path = item.get("path", "")
        if (
            not isinstance(path, str)
            or not path
            or "://" in path
            or path.startswith("/")
            or ".." in Path(path).parts
        ):
            raise SystemExit(f"asset path must be local and relative: {path!r}")
        if not item.get("license") or not item.get("attribution"):
            raise SystemExit(f"asset {path!r} needs license and attribution")
        candidate = ROOT / "assets" / path
        if not candidate.is_file():
            raise SystemExit(f"asset file is missing: {candidate}")
        digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
        if digest != item.get("sha256"):
            raise SystemExit(f"asset checksum mismatch: {path}")
    print(f"Asset manifest valid: {len(assets)} local asset(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
