from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from playwright.sync_api import Page, expect, sync_playwright
from pptx import Presentation


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture(scope="module")
def studio_url(tmp_path_factory: pytest.TempPathFactory):
    work = tmp_path_factory.mktemp("browser-studio")
    port = _free_port()
    env = {
        **os.environ,
        "GEMINI_API_KEY": "",
        "STORYBOARD_OUTPUT_DIR": str(work / "output"),
    }
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "storyboard_studio.cli",
            "serve",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=work,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}"
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        try:
            with urlopen(f"{url}/api/health", timeout=2) as response:
                if response.status == 200:
                    break
        except (URLError, OSError):
            time.sleep(0.1)
    else:
        process.terminate()
        raise RuntimeError("Packaged Storyboard Studio did not become ready")
    yield url
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def _assert_no_horizontal_overflow(page: Page) -> None:
    dimensions = page.evaluate(
        """() => ({
          viewport: window.innerWidth,
          root: document.documentElement.scrollWidth,
          body: document.body.scrollWidth,
        })"""
    )
    assert dimensions["root"] <= dimensions["viewport"]
    assert dimensions["body"] <= dimensions["viewport"]


def test_keyboard_authoring_export_and_responsive_contract(studio_url: str, tmp_path: Path):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.goto(studio_url, wait_until="domcontentloaded")

        page.keyboard.press("Tab")
        assert page.locator(":focus").inner_text() == "Skip to the presentation brief"

        sample = page.get_by_role("button", name="Try a sample brief")
        sample.focus()
        page.keyboard.press("Enter")
        assert "onboarding pilot" in page.get_by_label("Decision to make").input_value().lower()

        build = page.get_by_role("button", name="Build decision story")
        build.focus()
        page.keyboard.press("Enter")
        page.locator("#previewSection").wait_for(state="visible")
        assert page.locator("#previewSource").inner_text() == "LOCAL DECISION STORY"
        assert page.locator("#storyMap li").count() == 5

        page.get_by_role("button", name="Run Narrative Doctor").click()
        expect(page.locator("#doctorSummary")).not_to_contain_text("No diagnosis yet")
        first_findings = page.locator(".doctor-finding").count()
        assert first_findings >= 2
        page.get_by_role("button", name="Accept action").first.click()
        assert page.locator(":focus").get_attribute("aria-label") == "Evidence owner for slide 1"
        page.get_by_label("Evidence owner for slide 1").fill("Customer success lead")
        page.get_by_role("button", name="Run Narrative Doctor").click()
        expect(page.locator("#doctorSummary")).to_contain_text("1 notes")
        assert page.locator(".doctor-finding").count() < first_findings

        title = page.get_by_label("Presentation title")
        edited_title = "A practical plan to make remote onboarding feel human and measurable"
        title.fill(edited_title)
        title.press("Tab")
        assert "Unsaved storyboard edits" in page.locator("#saveStatus").inner_text()

        first_slide_title = page.get_by_label("Slide 1 title").input_value()
        page.get_by_role("button", name="Move slide down").first.click()
        assert page.get_by_label("Slide 2 title").input_value() == first_slide_title
        page.get_by_role("button", name="Undo").click()
        assert page.get_by_label("Slide 1 title").input_value() == first_slide_title
        page.get_by_role("button", name="Redo").click()
        assert page.get_by_label("Slide 2 title").input_value() == first_slide_title

        slide_total = page.locator("#storyMap li").count()
        preview_copy = [
            {
                "title": page.get_by_label(f"Slide {index} title").input_value(),
                "summary": page.get_by_label(f"Slide {index} summary").input_value(),
                "points": [
                    page.get_by_label(f"Slide {index} point {point}").input_value() for point in range(1, 4)
                ],
            }
            for index in range(1, slide_total + 1)
        ]
        role_labels = {
            "standard": "KEY FRAME",
            "comparison": "COMPARE",
            "decision": "DECISION",
            "timeline": "SEQUENCE",
            "metric": "SIGNAL",
        }
        preview_roles = [
            role_labels[
                page.locator("#deckPreview").get_by_label(f"Editorial block for slide {index}").input_value()
            ]
            for index in range(1, slide_total + 1)
        ]

        with page.expect_download() as download_event:
            page.get_by_role("button", name="Export PowerPoint").click()
        downloaded = tmp_path / "storyboard-browser-contract.pptx"
        download_event.value.save_as(downloaded)
        assert downloaded.read_bytes()[:2] == b"PK"
        exported = Presentation(downloaded)
        exported_text = [
            "\n".join(shape.text for shape in slide.shapes if shape.has_text_frame)
            for slide in exported.slides
        ]
        assert edited_title in exported_text[0]
        assert first_slide_title in exported_text[2]
        for slide_number, copy in enumerate(preview_copy, start=1):
            assert copy["title"] in exported_text[slide_number]
            assert copy["summary"] in exported_text[slide_number]
            assert all(point in exported_text[slide_number] for point in copy["points"])
            assert preview_roles[slide_number - 1] in exported_text[slide_number]

        with page.expect_download() as bundle_event:
            page.get_by_role("button", name="Export review bundle").click()
        bundle = tmp_path / "storyboard-review-bundle.zip"
        bundle_event.value.save_as(bundle)
        with zipfile.ZipFile(bundle) as archive:
            assert set(archive.namelist()) == {
                "deck.pptx",
                "deck.receipt.json",
                "deck.story.json",
            }

        for width in (320, 375, 1440):
            page.set_viewport_size({"width": width, "height": 900})
            _assert_no_horizontal_overflow(page)
            assert page.get_by_label("Presentation title").is_visible()
            assert page.get_by_role("button", name="Export PowerPoint").is_visible()

        title_metrics = title.evaluate(
            "element => ({scrollHeight: element.scrollHeight, clientHeight: element.clientHeight})"
        )
        assert title_metrics["scrollHeight"] <= title_metrics["clientHeight"] + 1
        assert not page.locator("#previewSection [aria-label]:not([type=hidden])").evaluate_all(
            "elements => elements.some(element => element.getClientRects().length === 0)"
        )
        browser.close()


def test_accessibility_errors_reduced_motion_and_import_recovery(studio_url: str, tmp_path: Path):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(studio_url, wait_until="domcontentloaded")

        page.get_by_role("button", name="Build decision story").click()
        error = page.get_by_role("alert")
        assert error.is_visible()
        assert "decision" in error.inner_text().lower()
        assert page.locator(":focus").get_attribute("id") == "decision"

        unnamed_controls = page.locator("input, textarea, select, button").evaluate_all(
            """elements => elements
              .filter(element => element.type !== "hidden" && !element.hidden)
              .filter(element => {
                const labelled = element.getAttribute("aria-label")
                  || element.getAttribute("aria-labelledby")
                  || (element.id && document.querySelector(`label[for="${element.id}"]`))
                  || element.closest("label")
                  || element.textContent.trim();
                return !labelled;
              })
              .map(element => element.outerHTML.slice(0, 120))"""
        )
        assert unnamed_controls == []

        contrast = page.evaluate(
            """() => {
              const rgb = value => {
                const hex = value.replace("#", "");
                return [0, 2, 4].map(index => parseInt(hex.slice(index, index + 2), 16) / 255);
              };
              const luminance = value => rgb(value)
                .map(channel => channel <= .03928 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4)
                .reduce((sum, channel, index) => sum + channel * [.2126, .7152, .0722][index], 0);
              const ratio = (first, second) => {
                const values = [luminance(first), luminance(second)].sort((a, b) => b - a);
                return (values[0] + .05) / (values[1] + .05);
              };
              return {
                body: ratio("#182321", "#f4f0e8"),
                action: ratio("#fffdf8", "#284a40"),
                muted: ratio("#5e6d67", "#fffdf8"),
              };
            }"""
        )
        assert min(contrast.values()) >= 4.5

        page.get_by_role("button", name="Try a sample brief").click()
        page.get_by_role("button", name="Build decision story").click()
        page.locator("#previewSection").wait_for(state="visible")
        invalid_outline = tmp_path / "invalid-outline.json"
        invalid_outline.write_text('{"title":"Missing slides"}', encoding="utf-8")
        page.locator("#importOutlineInput").set_input_files(invalid_outline)
        assert "Invalid outline" in page.locator("#saveStatus").inner_text()

        reduced_context = browser.new_context(reduced_motion="reduce")
        reduced_page = reduced_context.new_page()
        reduced_page.goto(studio_url, wait_until="domcontentloaded")
        reduced_state = reduced_page.evaluate(
            """() => ({
              matches: matchMedia("(prefers-reduced-motion: reduce)").matches,
              scrollBehavior: getComputedStyle(document.documentElement).scrollBehavior,
              transition: getComputedStyle(document.querySelector(".hero")).transitionDuration,
            })"""
        )
        assert reduced_state["matches"] is True
        assert reduced_state["scrollBehavior"] == "auto"
        transition_seconds = float(reduced_state["transition"].removesuffix("s"))
        assert transition_seconds <= 0.01
        reduced_context.close()
        browser.close()
