"""Render a PPTX to PDF/PNG for opt-in visual regression checks.

LibreOffice is intentionally an external QA dependency. The default test
suite remains portable; `--require` makes a missing viewer a hard failure in a
release-candidate job instead of hiding the gap.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a PPTX with LibreOffice for visual QA")
    parser.add_argument("pptx", type=Path)
    parser.add_argument("--output", type=Path, default=Path("rendered-slides"))
    parser.add_argument("--require", action="store_true", help="Fail when LibreOffice is unavailable")
    args = parser.parse_args()
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        message = "LibreOffice is unavailable; install the pinned viewer before visual QA."
        if args.require:
            raise SystemExit(message)
        print(f"SKIP: {message}")
        return 0

    args.output.mkdir(parents=True, exist_ok=True)
    version = subprocess.run([soffice, "--version"], capture_output=True, text=True, check=True)
    print(version.stdout.strip())
    subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(args.output), str(args.pptx)],
        check=True,
        capture_output=True,
        text=True,
    )
    pdf = args.output / f"{args.pptx.stem}.pdf"
    if not pdf.is_file():
        raise SystemExit(f"LibreOffice did not create {pdf}")
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm:
        subprocess.run(
            [pdftoppm, "-png", "-r", "144", str(pdf), str(args.output / args.pptx.stem)],
            check=True,
            capture_output=True,
            text=True,
        )
    print(f"Rendered {pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
