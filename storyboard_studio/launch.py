"""Local, proof-first launch-gate inspection.

The checker is intentionally conservative: it reports what the repository can
prove and leaves account ownership, user research, maintainer capacity, and
community publication as explicit gates. Network access is opt-in and limited
to the public PyPI metadata endpoint.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised by Python 3.10 CI
    import tomli as tomllib

GateStatus = Literal["passed", "blocked", "unverified"]


def _check(identifier: str, status: GateStatus, evidence: str, next_action: str) -> dict[str, str]:
    return {
        "id": identifier,
        "status": status,
        "evidence": evidence,
        "next_action": next_action,
    }


def _roadmap_counts(text: str) -> tuple[int, int]:
    marks = re.findall(r"^- \[([ x])\]", text, flags=re.MULTILINE)
    return marks.count("x"), marks.count(" ")


def _research_counts(text: str) -> tuple[int, int]:
    sessions_match = re.search(r"Consented first-success sessions\s*\|\s*(\d+)\s*\|\s*10", text)
    workflows_match = re.search(
        r"Real private workflows observed without collecting content\s*\|\s*(\d+)\s*\|\s*5", text
    )
    return (
        int(sessions_match.group(1)) if sessions_match else 0,
        int(workflows_match.group(1)) if workflows_match else 0,
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _report_file(root: Path, value: object, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty repository-relative path")
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"{field} must stay inside the repository")
    resolved = (root / candidate).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"{field} must stay inside the repository") from exc
    return resolved


def _viewer_report_status(root: Path) -> tuple[GateStatus, str]:
    """Verify the committed viewer report's source and screenshot digests."""

    directory = root / "docs" / "viewer-reports"
    reports = sorted(directory.glob("*.json"))
    if not reports:
        return "blocked", "No JSON viewer report is committed."
    fixture_count = 0
    screenshot_count = 0
    try:
        for report_path in reports:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or payload.get("schema_version") != "1":
                raise ValueError(f"{report_path.name} has an unsupported schema version")
            viewer = payload.get("viewer")
            if (
                not isinstance(viewer, dict)
                or not isinstance(viewer.get("name"), str)
                or not viewer["name"].strip()
                or not isinstance(viewer.get("version"), str)
                or not viewer["version"].strip()
            ):
                raise ValueError(f"{report_path.name} has incomplete viewer metadata")
            checked = payload.get("checked")
            if not isinstance(checked, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", checked):
                raise ValueError(f"{report_path.name} has an invalid checked date")
            commit = payload.get("commit")
            if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
                raise ValueError(f"{report_path.name} has an invalid source commit")
            fixtures = payload.get("fixtures")
            if not isinstance(fixtures, list) or not fixtures:
                raise ValueError(f"{report_path.name} has no fixtures")
            for fixture in fixtures:
                if not isinstance(fixture, dict):
                    raise ValueError(f"{report_path.name} contains a malformed fixture")
                source = _report_file(root, fixture.get("source"), "fixture.source")
                expected_source = fixture.get("source_sha256")
                if not isinstance(expected_source, str) or not re.fullmatch(r"[0-9a-f]{64}", expected_source):
                    raise ValueError(f"{report_path.name} contains an invalid source digest")
                if not source.is_file() or _sha256(source) != expected_source:
                    raise ValueError(f"{report_path.name} source digest does not match {source.name}")
                if fixture.get("result") != "PASS":
                    raise ValueError(f"{report_path.name} contains a non-PASS fixture result")
                pages = fixture.get("pages")
                if not isinstance(pages, int) or isinstance(pages, bool) or pages < 1:
                    raise ValueError(f"{report_path.name} contains an invalid page count")
                screenshots = fixture.get("screenshots")
                if not isinstance(screenshots, list) or not screenshots:
                    raise ValueError(f"{report_path.name} fixture has no screenshots")
                for screenshot in screenshots:
                    if not isinstance(screenshot, dict):
                        raise ValueError(f"{report_path.name} contains a malformed screenshot")
                    image = _report_file(root, screenshot.get("path"), "screenshot.path")
                    expected_image = screenshot.get("sha256")
                    if not isinstance(expected_image, str) or not re.fullmatch(
                        r"[0-9a-f]{64}", expected_image
                    ):
                        raise ValueError(f"{report_path.name} contains an invalid screenshot digest")
                    if not image.is_file() or _sha256(image) != expected_image:
                        raise ValueError(f"{report_path.name} screenshot digest does not match {image.name}")
                    if any(
                        not isinstance(screenshot.get(dimension), int)
                        or isinstance(screenshot.get(dimension), bool)
                        or screenshot[dimension] < 1
                        for dimension in ("width", "height")
                    ):
                        raise ValueError(f"{report_path.name} contains an invalid screenshot dimension")
                    screenshot_count += 1
                fixture_count += 1
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return "blocked", f"Viewer report validation failed: {exc}"
    return (
        "passed",
        f"{len(reports)} viewer report(s), {fixture_count} fixture(s), and "
        f"{screenshot_count} screenshot(s) are digest-verified.",
    )


def _release_evidence_status(root: Path) -> tuple[GateStatus, str]:
    """Check that the release workflow publishes the documented trust artifacts."""

    active_workflow_path = root / ".github" / "workflows" / "release.yml"
    paused_workflow_path = root / ".github" / "workflows-disabled" / "release.yml"
    workflow_path = active_workflow_path if active_workflow_path.is_file() else paused_workflow_path
    policy_path = root / "docs" / "RELEASE_POLICY.md"
    try:
        workflow = workflow_path.read_text(encoding="utf-8")
        policy = policy_path.read_text(encoding="utf-8")
    except OSError as exc:
        return "blocked", f"Release evidence policy could not be read: {exc}"
    required_workflow_fragments = (
        "SHA256SUMS",
        "SBOM.cdx.json",
        "storyboard-release-evidence",
        "actions/attest-build-provenance",
        "packages-dir: dist/",
        "scripts/validate_release_evidence.py",
    )
    missing = [fragment for fragment in required_workflow_fragments if fragment not in workflow]
    if missing:
        return "blocked", "Release workflow is missing: " + ", ".join(missing) + "."
    if "kept out of the PyPI upload" not in policy or "validate_release_evidence.py" not in policy:
        return "blocked", "Release policy does not document artifact validation and PyPI separation."
    if workflow_path == paused_workflow_path:
        return (
            "blocked",
            "Release definition with checksum/SBOM steps is preserved, but GitHub Actions are paused.",
        )
    return (
        "unverified",
        "Release definition is present; execution and downloaded checksum/SBOM evidence are unverified.",
    )


def _read_release_state(root: Path) -> dict[str, Any]:
    """Read declared intent separately from execution evidence."""
    path = root / "docs" / "release-state.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != "1":
        raise ValueError("Unsupported release-state manifest")
    if not isinstance(value.get("next_release"), str) or not re.fullmatch(
        r"\d+\.\d+\.\d+(?:[a-z0-9.-]+)?", value["next_release"]
    ):
        raise ValueError("Invalid next release version")
    claims = value.get("claims")
    if not isinstance(claims, list) or not claims:
        raise ValueError("Release state needs a claim inventory")
    identifiers: set[str] = set()
    for claim in claims:
        if not isinstance(claim, dict) or not isinstance(claim.get("id"), str):
            raise ValueError("Invalid release claim")
        if claim["id"] in identifiers:
            raise ValueError("Duplicate release claim")
        identifiers.add(claim["id"])
        for field in ("claim", "introduced_in"):
            if not isinstance(claim.get(field), str) or not claim[field].strip():
                raise ValueError(f"Claim needs {field}")
        if claim.get("evidence_state") != "source-present":
            raise ValueError("Claim inventory is not execution or publication evidence")
        for field in ("source", "test"):
            if not _report_file(root, claim.get(field), field).is_file():
                raise ValueError(f"Claim {claim['id']} has a missing {field}")
    gates = value.get("external_gates")
    if not isinstance(gates, dict) or any(
        not isinstance(gates.get(name), dict) for name in ("research", "maintainer", "launch")
    ):
        raise ValueError("Missing external gate records")
    return value


def _tag_status(root: Path, tag: str | None, version: str) -> tuple[GateStatus, str]:
    if tag is None:
        return "blocked", "No candidate tag supplied."
    if tag != f"v{version}":
        return "blocked", f"Tag {tag!r} does not match package version {version!r}."
    try:

        def git(*args: str) -> str:
            return subprocess.run(
                ["git", "-C", str(root), *args], check=True, capture_output=True, text=True, timeout=10
            ).stdout.strip()

        commit = git("rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}")
        if commit != git("rev-parse", "HEAD"):
            return "blocked", f"Tag {tag} exists but points to a different source commit."
        if git("status", "--porcelain"):
            return "blocked", "Working tree differs from the candidate tag; commit and revalidate first."
        return "passed", f"Local tag {tag} matches clean HEAD {commit}; remote publication is not checked."
    except (OSError, subprocess.SubprocessError):
        return "blocked", "Candidate tag does not exist locally or Git verification failed."


def _pypi_check(package_name: str, expected_version: str) -> tuple[GateStatus, str]:
    endpoint = f"https://pypi.org/pypi/{package_name}/{expected_version}/json"
    request = Request(endpoint, headers={"User-Agent": "storyboard-studio-launch-check/1"})
    try:
        with urlopen(request, timeout=8) as response:
            if response.status != 200:
                return "blocked", f"PyPI metadata returned HTTP {response.status}."
            payload = json.load(response)
    except HTTPError as exc:
        if exc.code == 404:
            return "blocked", "PyPI package endpoint returned HTTP 404; the project is not published."
        return "unverified", f"PyPI metadata request returned HTTP {exc.code}."
    except URLError as exc:
        return "unverified", f"PyPI metadata request failed: {exc.reason}."
    except (OSError, json.JSONDecodeError) as exc:
        return "unverified", f"PyPI metadata could not be read: {exc}."
    info = payload.get("info", {}) if isinstance(payload, dict) else {}
    version = info.get("version", "unknown") if isinstance(info, dict) else "unknown"
    if version != expected_version:
        return "blocked", "PyPI version does not match the candidate."
    return (
        "unverified",
        f"PyPI metadata for {version} exists; artifact download/install checks are still required.",
    )


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Launch gate",
        "",
        f"**Status:** `{report['status']}`  ",
        f"**Network:** `{report['network']}`",
        "",
        "| Gate | Status | Evidence | Next action |",
        "| --- | --- | --- | --- |",
    ]
    for gate in report["checks"]:
        lines.append(f"| `{gate['id']}` | `{gate['status']}` | {gate['evidence']} | {gate['next_action']} |")
    lines.extend(
        [
            "",
            "> This is a conservative repository check. A passing gate does not prove factual truth, "
            "user value, account ownership, or community acceptance.",
            "",
        ]
    )
    return "\n".join(lines)


def inspect_launch_gate(
    repository: str | Path = ".",
    *,
    release_tag: str | None = None,
    allow_network: bool = False,
) -> dict[str, Any]:
    """Inspect launch prerequisites without changing files or external state."""

    root = Path(repository).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Repository directory does not exist: {root}")
    roadmap_path = root / "ROADMAP.md"
    status_path = root / "docs" / "USER_RESEARCH_STATUS.md"
    pyproject_path = root / "pyproject.toml"
    roadmap = roadmap_path.read_text(encoding="utf-8")
    research_status = status_path.read_text(encoding="utf-8")
    package_version = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))["project"]["version"]
    checked, unchecked = _roadmap_counts(roadmap)
    sessions, workflows = _research_counts(research_status)
    try:
        release_state = _read_release_state(root)
        state_status: GateStatus = "passed"
        state_evidence = "Claim inventory paths exist; this is source presence only, not test execution."
    except (OSError, ValueError, TypeError):
        release_state = {}
        state_status = "blocked"
        state_evidence = "Release-state manifest is missing or invalid."

    required_proof = (
        root / "README.md",
        root / "docs" / "BENCHMARK.md",
        root / "SECURITY.md",
        root / "docs" / "USER_RESEARCH_PROTOCOL.md",
        root / "docs" / "assets" / "storyboard-demo-app-only.mp4",
        root / "docs" / "assets" / "storyboard-demo-app-only.gif",
        root / "docs" / "viewer-reports" / "libreoffice-26.8.0.3-macos-26.0.json",
        root / "docs" / "viewer-reports" / "assets" / "libreoffice-product-brief.png",
    )
    missing = [str(path.relative_to(root)) for path in required_proof if not path.is_file()]
    checks: list[dict[str, str]] = [
        _check(
            "claim-inventory", state_status, state_evidence, "Keep version/source/test boundaries current."
        )
    ]
    if missing:
        checks.append(
            _check(
                "proof-assets",
                "blocked",
                "Missing required proof files: " + ", ".join(missing),
                "Restore the named proof assets before promotion.",
            )
        )
    else:
        checks.append(
            _check(
                "proof-assets",
                "passed",
                "README, benchmark, security, research protocol, app-only demo, and viewer report "
                "assets are present.",
                "Keep the assets linked to the exact release tag.",
            )
        )

    viewer_status, viewer_evidence = _viewer_report_status(root)
    checks.append(
        _check(
            "viewer-proof",
            viewer_status,
            viewer_evidence,
            "Render the canonical fixtures with a named viewer and commit a digest-pinned report."
            if viewer_status != "passed"
            else "Keep the report tied to the renderer and viewer versions it records.",
        )
    )

    release_evidence_status, release_evidence = _release_evidence_status(root)
    checks.append(
        _check(
            "release-evidence",
            release_evidence_status,
            release_evidence,
            "Restore checksum, SBOM, attestation, and PyPI-separation steps before tagging."
            if release_evidence_status != "passed"
            else "Keep the evidence files generated from the exact tagged artifacts.",
        )
    )

    tag_status, tag_evidence = _tag_status(root, release_tag, str(package_version))
    checks.append(
        _check(
            "tagged-release",
            tag_status,
            tag_evidence,
            "Verify a real tag at the clean candidate SHA; publication is a separate gate.",
        )
    )

    if allow_network:
        pypi_status, pypi_evidence = _pypi_check("storyboard-studio", str(package_version))
        checks.append(
            _check(
                "pypi-publication",
                pypi_status,
                pypi_evidence,
                "Confirm the exact tagged wheel and Trusted Publisher if not passed.",
            )
        )
    else:
        checks.append(
            _check(
                "pypi-publication",
                "unverified",
                "Network check was not requested; PyPI ownership and publication are intentionally "
                "unverified.",
                "Run again with --allow-network after configuring Trusted Publishing.",
            )
        )

    if sessions >= 10 and workflows >= 5:
        research_gate: GateStatus = "unverified"
        research_evidence = (
            f"Research status reports {sessions}/10 sessions and {workflows}/5 real workflows."
        )
        research_action = (
            "Counts alone are not proof; review the consented aggregate and its source evidence."
        )
    else:
        research_gate = "blocked"
        research_evidence = (
            f"Research status reports {sessions}/10 sessions and {workflows}/5 real workflows."
        )
        research_action = (
            "Run only consented sessions under the published protocol; never count synthetic runs."
        )
    checks.append(_check("real-user-evidence", research_gate, research_evidence, research_action))

    external = release_state.get("external_gates", {})
    for identifier, name, action in (
        ("maintainer-capacity", "maintainer", "Confirm a named owner and response cadence with evidence."),
        ("launch-policy", "launch", "Review publication, research and community evidence before promotion."),
    ):
        record = external.get(name, {})
        pending = record.get("status") != "reviewed"
        checks.append(
            _check(
                identifier,
                "blocked" if pending else "unverified",
                "Structured gate is pending."
                if pending
                else "Review declared; external evidence still needs verification.",
                action,
            )
        )

    launch_status = "blocked" if any(check["status"] != "passed" for check in checks) else "ready"
    return {
        "schema_version": "1",
        "status": launch_status,
        "launchable": launch_status == "ready",
        "network": "pypi-read" if allow_network else "none",
        "repository": str(root),
        "package_version": str(package_version),
        "next_release": release_state.get("next_release"),
        "roadmap": {"checked": checked, "unchecked": unchecked},
        "checks": checks,
        "disclaimer": (
            "A launch gate reports repository evidence; it cannot prove factual truth, user value, account "
            "ownership, or acceptance by an external community."
        ),
    }


def write_launch_report(
    report: dict[str, Any],
    output: str | Path | None = None,
    *,
    format: Literal["json", "markdown"] = "markdown",
) -> None:
    """Print or write a launch-gate report."""

    content = (
        json.dumps(report, indent=2, ensure_ascii=False) + "\n" if format == "json" else _markdown(report)
    )
    if output is None:
        print(content, end="")
        return
    destination = Path(output).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    print(f"Created {destination}")


__all__ = ["inspect_launch_gate", "write_launch_report"]
