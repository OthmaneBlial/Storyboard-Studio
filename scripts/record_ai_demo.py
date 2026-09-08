"""Capture the real local browser workflow for the private AI showcase.

The recorder uses Playwright's Chromium video capture and never opens an Office
application.  It exercises the same buttons a user sees: sample brief, local
story build, Narrative Doctor, author fix, and PowerPoint export.
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(url: str, timeout: float = 20) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(f"{url}/api/health", timeout=2) as response:
                if response.status == 200:
                    return
        except (URLError, OSError):
            time.sleep(0.1)
    raise RuntimeError("Storyboard Studio did not become ready for recording.")


def record(output: Path) -> None:
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    with tempfile.TemporaryDirectory(prefix="storyboard-ai-demo-") as temporary:
        work = Path(temporary)
        server = subprocess.Popen(
            [
                str(ROOT / ".venv" / "bin" / "storyboard"),
                "serve",
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
            ],
            cwd=work,
            env={
                **os.environ,
                "GEMINI_API_KEY": "",
                "STORYBOARD_OUTPUT_DIR": str(work / "output"),
            },
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            wait_for_server(url)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={"width": 1280, "height": 720},
                    device_scale_factor=1,
                    record_video_dir=str(work / "video"),
                    record_video_size={"width": 1280, "height": 720},
                    accept_downloads=True,
                )
                page = context.new_page()
                page.goto(url, wait_until="networkidle")
                time.sleep(2)
                page.get_by_role("button", name="Try a sample brief").click()
                time.sleep(2)
                page.get_by_role("button", name="Build decision story").click()
                page.locator("#previewSection").wait_for(state="visible")
                page.locator("#narrativeReview").scroll_into_view_if_needed()
                time.sleep(2)
                page.get_by_role("button", name="Run Narrative Doctor").click()
                expect(page.locator("#doctorSummary")).not_to_contain_text("No diagnosis yet")
                time.sleep(2)
                page.get_by_role("button", name="Accept action").first.click()
                page.get_by_label("Evidence owner for slide 1").fill("AI program lead")
                page.get_by_role("button", name="Run Narrative Doctor").click()
                expect(page.locator("#doctorSummary")).to_contain_text("notes")
                time.sleep(2)
                page.locator(".preview-heading").scroll_into_view_if_needed()
                with page.expect_download() as download_event:
                    page.get_by_role("button", name="Export PowerPoint").click()
                download_event.value.save_as(work / "private-ai-review.pptx")
                time.sleep(3)
                page.locator("#deckPreview").scroll_into_view_if_needed()
                time.sleep(3)
                context.close()
                browser.close()
                recordings = sorted((work / "video").glob("*.webm"))
                if len(recordings) != 1:
                    raise RuntimeError(f"Expected one Playwright recording, found {len(recordings)}")
                output.write_bytes(recordings[0].read_bytes())
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    record(args.output)
    print(f"Recorded browser workflow {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
