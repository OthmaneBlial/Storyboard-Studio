"""Validate versioned, reproducible viewer-compatibility reports.

Viewer reports are evidence records, not claims that a ZIP inspection or one
viewer proves compatibility everywhere.  Each report pins the viewer version,
source fixture digest, rendered page count, and committed screenshot digests so
future changes cannot silently replace the evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "docs" / "viewer-reports"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _repo_path(value: Any, *, repository: Path, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty repository-relative path")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{field} must stay inside the repository")
    resolved = (repository / candidate).resolve()
    try:
        resolved.relative_to(repository.resolve())
    except ValueError as exc:
        raise ValueError(f"{field} must stay inside the repository") from exc
    return resolved


def _required_text(mapping: dict[str, Any], key: str, context: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{context}.{key} must be a non-empty string")
    return value.strip()


def validate_report_file(report_path: str | Path, repository: str | Path = ROOT) -> dict[str, Any]:
    """Validate one report and return a compact summary.

    The function intentionally checks committed evidence only.  It does not
    launch a viewer or infer a PASS from a missing screenshot.
    """

    report_file = Path(report_path).expanduser().resolve()
    root = Path(repository).expanduser().resolve()
    try:
        payload = json.loads(report_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{report_file}: invalid JSON ({exc})") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{report_file}: report must be a JSON object")
    if payload.get("schema_version") != "1":
        raise ValueError(f"{report_file}: schema_version must be '1'")

    viewer = payload.get("viewer")
    if not isinstance(viewer, dict):
        raise ValueError(f"{report_file}: viewer must be an object")
    viewer_name = _required_text(viewer, "name", "viewer")
    viewer_version = _required_text(viewer, "version", "viewer")

    platform = payload.get("platform")
    if not isinstance(platform, dict):
        raise ValueError(f"{report_file}: platform must be an object")
    _required_text(platform, "os", "platform")
    _required_text(platform, "architecture", "platform")

    checked = _required_text(payload, "checked", "report")
    try:
        date.fromisoformat(checked)
    except ValueError as exc:
        raise ValueError(f"{report_file}: checked must be YYYY-MM-DD") from exc
    commit = _required_text(payload, "commit", "report")
    if not COMMIT.fullmatch(commit):
        raise ValueError(f"{report_file}: commit must be a 40-character lowercase SHA")

    method = payload.get("method")
    if not isinstance(method, dict):
        raise ValueError(f"{report_file}: method must be an object")
    _required_text(method, "command", "method")
    _required_text(method, "mode", "method")

    fixtures = payload.get("fixtures")
    if not isinstance(fixtures, list) or not fixtures:
        raise ValueError(f"{report_file}: fixtures must be a non-empty array")
    fixture_summaries: list[dict[str, Any]] = []
    for index, fixture in enumerate(fixtures):
        context = f"fixtures[{index}]"
        if not isinstance(fixture, dict):
            raise ValueError(f"{report_file}: {context} must be an object")
        source = _repo_path(fixture.get("source"), repository=root, field=f"{context}.source")
        if not source.is_file():
            raise ValueError(f"{report_file}: {context}.source does not exist: {source}")
        source_sha256 = _required_text(fixture, "source_sha256", context)
        if not SHA256.fullmatch(source_sha256):
            raise ValueError(f"{report_file}: {context}.source_sha256 must be lowercase SHA-256")
        actual_source_sha256 = _digest(source)
        if actual_source_sha256 != source_sha256:
            raise ValueError(
                f"{report_file}: {context}.source_sha256 does not match {source.relative_to(root)}"
            )
        pages = fixture.get("pages")
        if not isinstance(pages, int) or isinstance(pages, bool) or pages < 1:
            raise ValueError(f"{report_file}: {context}.pages must be a positive integer")
        if fixture.get("result") != "PASS":
            raise ValueError(f"{report_file}: {context}.result must be PASS for committed evidence")
        checks = fixture.get("checks")
        if not isinstance(checks, list) or not checks or not all(isinstance(item, str) for item in checks):
            raise ValueError(f"{report_file}: {context}.checks must contain one or more strings")

        screenshots = fixture.get("screenshots")
        if not isinstance(screenshots, list) or not screenshots:
            raise ValueError(f"{report_file}: {context}.screenshots must be a non-empty array")
        screenshot_summaries: list[dict[str, Any]] = []
        for screenshot_index, screenshot in enumerate(screenshots):
            screenshot_context = f"{context}.screenshots[{screenshot_index}]"
            if not isinstance(screenshot, dict):
                raise ValueError(f"{report_file}: {screenshot_context} must be an object")
            screenshot_path = _repo_path(
                screenshot.get("path"), repository=root, field=f"{screenshot_context}.path"
            )
            if not screenshot_path.is_file():
                raise ValueError(f"{report_file}: screenshot does not exist: {screenshot_path}")
            screenshot_sha256 = _required_text(screenshot, "sha256", screenshot_context)
            if not SHA256.fullmatch(screenshot_sha256):
                raise ValueError(f"{report_file}: {screenshot_context}.sha256 must be lowercase SHA-256")
            if _digest(screenshot_path) != screenshot_sha256:
                raise ValueError(f"{report_file}: {screenshot_context}.sha256 does not match the file")
            for dimension in ("width", "height"):
                value = screenshot.get(dimension)
                if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                    raise ValueError(f"{report_file}: {screenshot_context}.{dimension} must be positive")
            screenshot_summaries.append(
                {
                    "path": str(screenshot_path.relative_to(root)),
                    "width": screenshot["width"],
                    "height": screenshot["height"],
                }
            )
        fixture_summaries.append(
            {
                "source": str(source.relative_to(root)),
                "pages": pages,
                "screenshots": screenshot_summaries,
            }
        )

    return {
        "report": str(report_file.relative_to(root))
        if report_file.is_relative_to(root)
        else str(report_file),
        "viewer": f"{viewer_name} {viewer_version}",
        "checked": checked,
        "commit": commit,
        "fixtures": fixture_summaries,
    }


def validate_report_directory(
    report_directory: str | Path = REPORT_DIR, repository: str | Path = ROOT
) -> list[dict[str, Any]]:
    """Validate every JSON viewer report in a directory."""

    directory = Path(report_directory).expanduser().resolve()
    reports = sorted(directory.glob("*.json"))
    if not reports:
        raise ValueError(f"No viewer reports found in {directory}")
    return [validate_report_file(report, repository) for report in reports]


def main() -> int:
    try:
        summaries = validate_report_directory()
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    fixture_count = sum(len(summary["fixtures"]) for summary in summaries)
    screenshot_count = sum(
        len(fixture["screenshots"]) for summary in summaries for fixture in summary["fixtures"]
    )
    print(
        f"Viewer reports valid: {len(summaries)} report(s), {fixture_count} fixture(s), "
        f"{screenshot_count} screenshot(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
