"""Exercise the documented local HTTP workflow against a disposable server."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _request(url: str, method: str = "GET", payload: dict | None = None) -> tuple[int, bytes]:
    body = json.dumps(payload).encode() if payload is not None else None
    request = Request(url, data=body, method=method, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=10) as response:
        return response.status, response.read()


def main() -> int:
    port = _free_port()
    env = {**os.environ, "GEMINI_API_KEY": ""}
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    export_id: str | None = None
    try:
        base = f"http://127.0.0.1:{port}"
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                status, _ = _request(f"{base}/api/health")
                if status == 200:
                    break
            except (URLError, OSError):
                time.sleep(0.1)
        else:
            raise RuntimeError("local server did not become ready")

        fixture = {
            "topic": "A calm, private presentation workflow",
            "brief": "Show how a small team can move from idea to an editable decision brief.",
            "slide_count": 3,
            "use_ai": False,
        }
        status, body = _request(f"{base}/api/content", "POST", fixture)
        if status != 200:
            raise RuntimeError(f"content endpoint returned HTTP {status}")
        outline = json.loads(body)
        if outline.get("source") != "local":
            raise RuntimeError("smoke fixture unexpectedly used a remote provider")

        status, body = _request(
            f"{base}/api/presentations", "POST", {"presentation": outline["presentation"]}
        )
        if status != 201:
            raise RuntimeError(f"export endpoint returned HTTP {status}")
        export = json.loads(body)
        export_id = export["id"]
        status, pptx = _request(f"{base}{export['download_url']}")
        if status != 200 or pptx[:2] != b"PK":
            raise RuntimeError("downloaded export was not a valid PPTX archive")
        print(f"Smoke passed: local outline and editable PPTX export ({len(pptx):,} bytes).")
        return 0
    finally:
        if export_id:
            generated = ROOT / "output" / f"{export_id}.pptx"
            generated.unlink(missing_ok=True)
        process.send_signal(signal.SIGTERM)
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
