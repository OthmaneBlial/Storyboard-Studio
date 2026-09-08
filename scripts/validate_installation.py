"""Install each distribution independently and exercise it outside the checkout."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import platform
import socket
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import ProxyHandler, Request, build_opener


def validate_installation(archive: Path, extras: str = "") -> dict:
    archive = archive.resolve()
    with tempfile.TemporaryDirectory(prefix="storyboard install é ") as temporary:
        root = Path(temporary)
        env_dir = root / "venv"
        cwd = root / "empty working directory"
        cwd.mkdir()
        env = {k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "PYTHONHOME", "GEMINI_API_KEY"}}
        env["STORYBOARD_OUTPUT_DIR"] = str(root / "cache")
        env["PYTHONNOUSERSITE"] = "1"
        subprocess.run([sys.executable, "-m", "venv", str(env_dir)], check=True, env=env)
        python = env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        started = time.monotonic()
        installed = subprocess.run(
            [str(python), "-m", "pip", "install", str(archive) + (f"[{extras}]" if extras else "")],
            cwd=cwd,
            env=env,
            text=True,
            capture_output=True,
        )
        if installed.returncode:
            raise RuntimeError(installed.stderr)
        install_seconds = round(time.monotonic() - started, 2)

        def cli(*args: str) -> str:
            return subprocess.run(
                [str(python), "-m", "storyboard_studio.cli", *args],
                cwd=cwd,
                env=env,
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            ).stdout

        version = cli("--version").strip()
        subprocess.run(
            [
                str(python),
                "-c",
                "import storyboard_studio.cli, sys; "
                "assert 'cairosvg' not in sys.modules; assert 'google.genai' not in sys.modules",
            ],
            cwd=cwd,
            env=env,
            check=True,
            timeout=30,
        )
        if extras:
            subprocess.run(
                [
                    str(python),
                    "-c",
                    "import cairosvg; from google import genai; "
                    'assert cairosvg.svg2png(bytestring=b\'<svg xmlns="http://www.w3.org/2000/svg" '
                    'width="10" height="10"/>\').startswith(b\'\\x89PNG\')',
                ],
                cwd=cwd,
                env=env,
                check=True,
                timeout=30,
            )
        cli("demo", "--bundle", "--output", "demo.pptx")
        cli("verify", "demo.receipt.json")
        csv_bytes = b"category,value\nOne,2\nTwo,5\n"
        (cwd / "observations.csv").write_bytes(csv_bytes)
        portable_story = json.loads((cwd / "demo.story.json").read_text(encoding="utf-8"))
        portable_story["presentation"]["assets"] = [
            {
                "id": "installed-data",
                "kind": "data",
                "path": "observations.csv",
                "sha256": hashlib.sha256(csv_bytes).hexdigest(),
                "media_type": "text/csv",
                "license": "CC0-1.0",
                "attribution": "Synthetic installation check",
                "source_note": "Synthetic observations; no customer data",
            }
        ]
        slide = portable_story["presentation"]["slides"][0]
        slide["block"] = "chart"
        slide["content_block"] = {
            "type": "chart",
            "chart_type": "bar",
            "asset_id": "installed-data",
            "category_field": "category",
            "value_fields": ["value"],
            "title": "Installed chart",
            "source_note": "Synthetic installation check",
        }
        (cwd / "portable.story.json").write_text(json.dumps(portable_story), encoding="utf-8")
        cli("project", "pack", "--input", "portable.story.json", "--output", "portable.zip", "--render")
        cli("project", "open", "--input", "portable.zip", "--output", "reopened")
        cli("export", "--input", "reopened/deck.story.json", "--output", "reopened.pptx", "--bundle")
        cli("verify", "reopened.receipt.json")
        with zipfile.ZipFile(cwd / "reopened.pptx") as rendered:
            if "ppt/charts/chart1.xml" not in rendered.namelist():
                raise RuntimeError("Installed portable project did not regenerate its native chart")
        packages = json.loads(
            subprocess.check_output(
                [str(python), "-m", "pip", "list", "--format=json"],
                cwd=cwd,
                env=env,
                text=True,
            )
        )
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        opener = build_opener(ProxyHandler({}))
        base = f"http://127.0.0.1:{port}"

        def request(path: str, payload: dict | None = None) -> bytes:
            body = json.dumps(payload).encode() if payload is not None else None
            with opener.open(
                Request(base + path, data=body, headers={"Content-Type": "application/json"}), timeout=10
            ) as response:
                return response.read()

        with (root / "server.log").open("w+") as log:
            process = subprocess.Popen(
                [str(python), "-m", "storyboard_studio.cli", "serve", "--port", str(port)],
                cwd=cwd,
                env=env,
                stdout=log,
                stderr=log,
            )
            try:
                deadline = time.monotonic() + 20
                while time.monotonic() < deadline:
                    try:
                        request("/api/health")
                        break
                    except (OSError, URLError):
                        if process.poll() is not None:
                            log.seek(0)
                            raise RuntimeError(log.read()) from None
                        time.sleep(0.1)
                else:
                    raise RuntimeError("Installed server did not become ready")
                if b"<html" not in request("/").lower():
                    raise RuntimeError("Packaged web application missing")
                request("/static/app.js")
                request("/static/projects.js")
                outline = json.loads(
                    request(
                        "/api/content",
                        {
                            "topic": "Clean installation",
                            "brief": "Validate local editable output",
                            "slide_count": 3,
                            "use_ai": False,
                        },
                    )
                )
                if outline.get("source") != "local":
                    raise RuntimeError("Expected offline provider")
                exported = json.loads(
                    request("/api/presentations", {"presentation": outline["presentation"]})
                )
                with zipfile.ZipFile(io.BytesIO(request(exported["download_url"]))) as pptx:
                    if "ppt/presentation.xml" not in pptx.namelist() or pptx.testzip():
                        raise RuntimeError("Invalid installed HTTP export")
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
        return {
            "archive": archive.name,
            "extras": extras,
            "version": version,
            "platform": platform.platform(),
            "python": platform.python_version(),
            "install_seconds": install_seconds,
            "environment_bytes": sum(p.stat().st_size for p in env_dir.rglob("*") if p.is_file()),
            "packages": packages,
            "checks": [
                "version",
                "demo-bundle",
                "verify",
                "web",
                "local-provider",
                "http-pptx",
                "portable-csv-pack-open-export",
            ],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", type=Path, nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--extras", choices=["", "gemini,svg"], default="")
    args = parser.parse_args()
    results = []
    for archive in args.archives:
        results.append(validate_installation(archive, args.extras))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(f"Installed workflow passed: {archive.name}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
