import json
from pathlib import Path

import pytest

from scripts.validate_viewer_reports import validate_report_directory, validate_report_file

ROOT = Path(__file__).resolve().parents[1]


def test_committed_viewer_report_pins_sources_and_screenshots():
    summaries = validate_report_directory()

    latest = next(summary for summary in summaries if summary["report"].endswith("2026-09-08.json"))
    assert latest["viewer"] == "LibreOffice Impress 26.8.0.3"
    assert len(latest["fixtures"]) == 6
    assert sum(len(item["screenshots"]) for item in latest["fixtures"]) == 6


def test_viewer_report_rejects_a_changed_screenshot_digest(tmp_path: Path):
    source = ROOT / "docs/viewer-reports/libreoffice-26.8.0.3-macos-26.0.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["fixtures"][0]["screenshots"][0]["sha256"] = "0" * 64
    candidate = tmp_path / "report.json"
    candidate.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="sha256 does not match"):
        validate_report_file(candidate, ROOT)
