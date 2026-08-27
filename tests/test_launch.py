import hashlib
import json
from pathlib import Path

import pytest

from storyboard_studio.cli import main
from storyboard_studio.launch import _viewer_report_status, inspect_launch_gate, write_launch_report


def test_launch_gate_is_conservative_for_the_current_repository():
    report = inspect_launch_gate(Path("."))

    assert report["status"] == "blocked"
    assert report["launchable"] is False
    assert report["network"] == "none"
    assert report["roadmap"]["unchecked"] == 11
    checks = {check["id"]: check for check in report["checks"]}
    assert checks["proof-assets"]["status"] == "passed"
    assert "viewer report" in checks["proof-assets"]["evidence"]
    assert checks["viewer-proof"]["status"] == "passed"
    assert "digest-verified" in checks["viewer-proof"]["evidence"]
    assert checks["tagged-release"]["status"] == "blocked"
    assert checks["pypi-publication"]["status"] == "unverified"
    assert checks["real-user-evidence"]["status"] == "blocked"
    assert checks["maintainer-capacity"]["status"] == "blocked"


def test_launch_gate_accepts_only_the_exact_package_tag(tmp_path: Path):
    report = inspect_launch_gate(Path("."), release_tag="v0.2.0")
    checks = {check["id"]: check for check in report["checks"]}
    assert checks["tagged-release"]["status"] == "passed"

    mismatch = inspect_launch_gate(Path("."), release_tag="v9.9.9")
    mismatch_checks = {check["id"]: check for check in mismatch["checks"]}
    assert mismatch_checks["tagged-release"]["status"] == "blocked"

    with pytest.raises(ValueError, match="does not exist"):
        inspect_launch_gate(tmp_path / "missing")


def test_launch_report_supports_json_markdown_and_fail_on_blocked(tmp_path: Path):
    report_path = tmp_path / "launch.json"
    assert main(["launch-check", "--format", "json", "--output", str(report_path)]) == 0
    value = json.loads(report_path.read_text(encoding="utf-8"))
    assert value["status"] == "blocked"

    markdown_path = tmp_path / "launch.md"
    write_launch_report(value, markdown_path, format="markdown")
    assert "# Launch gate" in markdown_path.read_text(encoding="utf-8")
    assert main(["launch-check", "--fail-on-blocked"]) == 1


def test_launch_gate_rejects_a_non_pass_viewer_report(tmp_path: Path):
    source = tmp_path / "fixture.json"
    source.write_text("{}", encoding="utf-8")
    screenshot = tmp_path / "capture.png"
    screenshot.write_bytes(b"synthetic screenshot")
    report_dir = tmp_path / "docs" / "viewer-reports"
    report_dir.mkdir(parents=True)
    payload = {
        "schema_version": "1",
        "viewer": {"name": "Fixture Viewer", "version": "1.0"},
        "checked": "2026-08-27",
        "commit": "a" * 40,
        "fixtures": [
            {
                "source": "fixture.json",
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "pages": 1,
                "result": "FAIL",
                "screenshots": [
                    {
                        "path": "capture.png",
                        "sha256": hashlib.sha256(screenshot.read_bytes()).hexdigest(),
                        "width": 1,
                        "height": 1,
                    }
                ],
            }
        ],
    }
    (report_dir / "report.json").write_text(json.dumps(payload), encoding="utf-8")

    status, evidence = _viewer_report_status(tmp_path)

    assert status == "blocked"
    assert "non-PASS" in evidence
