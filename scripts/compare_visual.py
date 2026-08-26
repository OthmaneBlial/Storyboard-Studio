"""Compare two reviewed PNG renders with a small, explicit pixel tolerance."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageStat


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare rendered slide PNGs")
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--tolerance", type=float, default=12.0)
    args = parser.parse_args()
    baseline = Image.open(args.baseline).convert("RGB")
    candidate = Image.open(args.candidate).convert("RGB").resize(baseline.size)
    error = sum(ImageStat.Stat(ImageChops.difference(baseline, candidate)).mean) / 3
    print(f"visual mean absolute error: {error:.2f} (tolerance: {args.tolerance:.2f})")
    if error > args.tolerance:
        raise SystemExit("visual regression exceeds the reviewed tolerance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
