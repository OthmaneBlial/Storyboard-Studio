"""Record the synthetic browser-to-editable-viewer proof on macOS.

The capture is deliberately constrained to the foreground application surface.
It must never include the macOS menu bar, Dock, desktop, or background windows.
"""

from __future__ import annotations

import argparse
import os
import signal
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
APP_WINDOW_POSITION = (0, 29)
APP_WINDOW_SIZE = (1280, 691)


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(url: str, timeout: float = 15) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(f"{url}/api/health", timeout=2) as response:
                if response.status == 200:
                    return
        except (URLError, OSError):
            time.sleep(0.1)
    raise RuntimeError("Storyboard Studio did not become ready for recording.")


def applescript(*lines: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    command = ["osascript"]
    for line in lines:
        command.extend(("-e", line))
    return subprocess.run(command, check=check, capture_output=True, text=True)


def libreoffice_is_running() -> bool:
    result = subprocess.run(
        ["pgrep", "-f", "/Applications/LibreOffice.app/Contents/MacOS/soffice"],
        check=False,
        capture_output=True,
    )
    return result.returncode == 0


def close_recorded_libreoffice() -> None:
    applescript(
        'tell application "System Events" to tell process "LibreOffice"',
        'keystroke "q" using command down',
        "delay 1",
        "key code 48 using shift down",
        "key code 48 using shift down",
        "key code 36",
        "end tell",
        check=False,
    )


def foreground_window_id(process_name: str) -> str:
    """Return the focused macOS window id, failing closed if Accessibility denies it."""
    result = applescript(
        f'tell application "System Events" to tell process "{process_name}" '
        'to get value of attribute "AXWindowNumber" of front window',
        check=False,
    )
    window_id = result.stdout.strip()
    if result.returncode != 0 or not window_id.isdigit():
        raise RuntimeError(
            f"Could not resolve the foreground {process_name} window id; refusing an unrestricted capture."
        )
    return window_id


def start_app_capture(output: Path, process_name: str) -> subprocess.Popen[bytes]:
    """Record one foreground window; never fall back to a display or rectangle capture."""
    window_id = foreground_window_id(process_name)
    return subprocess.Popen(["/usr/sbin/screencapture", "-v", "-l", window_id, "-o", "-k", str(output)])


def stop_app_capture(recorder: subprocess.Popen[bytes]) -> None:
    recorder.send_signal(signal.SIGINT)
    recorder.wait(timeout=15)


def record(output: Path) -> None:
    if os.uname().sysname != "Darwin":
        raise RuntimeError("The proof recorder currently requires macOS screencapture.")
    if libreoffice_is_running():
        raise RuntimeError("Close LibreOffice before recording so existing work is not touched.")
    output = output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    port = free_port()
    url = f"http://127.0.0.1:{port}"

    with tempfile.TemporaryDirectory(prefix="storyboard-demo-") as temporary:
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
            env={**os.environ, "GEMINI_API_KEY": "", "STORYBOARD_OUTPUT_DIR": str(work / "output")},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        recorder: subprocess.Popen[bytes] | None = None
        browser = None
        try:
            wait_for_server(url)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=False, slow_mo=120)
                context = browser.new_context(no_viewport=True, accept_downloads=True)
                page = context.new_page()
                page.goto(url, wait_until="domcontentloaded")
                applescript(
                    'tell application "System Events" to tell process "Chromium"',
                    "set frontmost to true",
                    f"set position of front window to {{{APP_WINDOW_POSITION[0]}, {APP_WINDOW_POSITION[1]}}}",
                    f"set size of front window to {{{APP_WINDOW_SIZE[0]}, {APP_WINDOW_SIZE[1]}}}",
                    "end tell",
                    check=False,
                )
                page.locator(".hero").scroll_into_view_if_needed()
                browser_movie = work / "browser.mov"
                recorder = start_app_capture(browser_movie, "Chromium")
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
                page.get_by_label("Evidence owner for slide 1").fill("Customer success lead")
                page.get_by_role("button", name="Run Narrative Doctor").click()
                expect(page.locator("#doctorSummary")).to_contain_text("1 notes")
                time.sleep(2)
                page.locator(".preview-heading").scroll_into_view_if_needed()
                with page.expect_download() as download_event:
                    page.get_by_role("button", name="Export PowerPoint").click()
                presentation = work / "storyboard-demo.pptx"
                download_event.value.save_as(presentation)
                time.sleep(2)
                stop_app_capture(recorder)
                recorder = None
                subprocess.run(["open", "-a", "LibreOffice", str(presentation)], check=True)
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    windows = applescript(
                        (
                            'tell application "System Events" to tell process "LibreOffice" '
                            "to get name of every window"
                        ),
                        check=False,
                    )
                    result = applescript(
                        (
                            'tell application "System Events" to tell process "LibreOffice" '
                            "to get name of front window"
                        ),
                        check=False,
                    )
                    if result.returncode == 0 and ".pptx" in result.stdout:
                        break
                    if windows.returncode == 0 and ".pptx" in windows.stdout:
                        applescript(
                            'tell application "System Events" to tell process "LibreOffice" to key code 53',
                            check=False,
                        )
                    time.sleep(0.5)
                else:
                    raise RuntimeError("LibreOffice did not open the synthetic PPTX.")
                applescript(
                    'tell application "System Events" to tell process "LibreOffice"',
                    "set frontmost to true",
                    f"set position of front window to {{{APP_WINDOW_POSITION[0]}, {APP_WINDOW_POSITION[1]}}}",
                    f"set size of front window to {{{APP_WINDOW_SIZE[0]}, {APP_WINDOW_SIZE[1]}}}",
                    "key code 53",
                    "end tell",
                )
                viewer_movie = work / "viewer.mov"
                recorder = start_app_capture(viewer_movie, "LibreOffice")
                time.sleep(2)
                applescript(
                    'tell application "System Events" to tell process "LibreOffice"',
                    "set frontmost to true",
                    "key code 48",
                    "key code 48",
                    "key code 48",
                    "key code 48",
                    "key code 48",
                    "key code 48",
                    "delay 2",
                    "key code 120",
                    "delay 0.5",
                    'keystroke "a" using command down',
                    'keystroke "Onboarding pilot - reviewed live"',
                    "delay 4",
                    "end tell",
                )
                stop_app_capture(recorder)
                recorder = None
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-i",
                        str(browser_movie),
                        "-i",
                        str(viewer_movie),
                        "-filter_complex",
                        (
                            "[0:v]setpts=PTS-STARTPTS[first];"
                            "[1:v]setpts=PTS-STARTPTS[second];"
                            "[first][second]concat=n=2:v=1:a=0[out]"
                        ),
                        "-map",
                        "[out]",
                        "-c:v",
                        "libx264",
                        "-preset",
                        "slow",
                        "-crf",
                        "23",
                        "-pix_fmt",
                        "yuv420p",
                        "-movflags",
                        "+faststart",
                        str(output),
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        finally:
            if recorder and recorder.poll() is None:
                stop_app_capture(recorder)
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass
            close_recorded_libreoffice()
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "docs" / "assets" / "storyboard-demo-app-only.mp4",
    )
    args = parser.parse_args()
    record(args.output)
    print(f"Recorded {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
