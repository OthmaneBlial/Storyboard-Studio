import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from storyboard_studio.cli import main
from storyboard_studio.launch import (
    _read_release_state,
    _release_evidence_status,
    _tag_status,
    _viewer_report_status,
    inspect_launch_gate,
    write_launch_report,
)


def test_launch_gate_is_conservative_for_the_current_repository():
    report = inspect_launch_gate(Path("."))

    assert report["status"] == "blocked"
    assert report["launchable"] is False
    assert report["network"] == "none"
    assert isinstance(report["roadmap"]["unchecked"], int)
    checks = {check["id"]: check for check in report["checks"]}
    assert checks["proof-assets"]["status"] == "passed"
    assert "viewer report" in checks["proof-assets"]["evidence"]
    assert checks["viewer-proof"]["status"] == "passed"
    assert "digest-verified" in checks["viewer-proof"]["evidence"]
    assert checks["release-evidence"]["status"] == "unverified"
    assert "execution" in checks["release-evidence"]["evidence"]
    assert checks["tagged-release"]["status"] == "blocked"
    assert checks["pypi-publication"]["status"] == "unverified"
    assert checks["real-user-evidence"]["status"] == "blocked"
    assert checks["maintainer-capacity"]["status"] == "blocked"


def test_launch_gate_requires_the_current_ai_proof_assets(tmp_path: Path):
    import shutil

    repository = tmp_path / "repository"
    shutil.copytree(
        ".",
        repository,
        ignore=shutil.ignore_patterns(".git", ".venv", "dist", "build", "output", "__pycache__"),
    )
    (repository / "docs" / "assets" / "storyboard-demo-ai.mp4").unlink()

    report = inspect_launch_gate(repository)

    proof = next(check for check in report["checks"] if check["id"] == "proof-assets")
    assert proof["status"] == "blocked"
    assert "storyboard-demo-ai.mp4" in proof["evidence"]


def test_launch_gate_checks_actual_tag_commit_and_clean_worktree(tmp_path: Path):
    def git(*args):
        return subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True, text=True)

    git("init")
    (tmp_path / "version.txt").write_text("0.2.0")
    git("add", ".")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "fixture")
    assert _tag_status(tmp_path, "v0.2.0", "0.2.0")[0] == "blocked"
    git("tag", "v0.2.0")
    assert _tag_status(tmp_path, "v0.2.0", "0.2.0")[0] == "passed"
    assert _tag_status(tmp_path, "v9.9.9", "0.2.0")[0] == "blocked"
    (tmp_path / "version.txt").write_text("changed")
    assert _tag_status(tmp_path, "v0.2.0", "0.2.0")[0] == "blocked"
    git("add", ".")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "new source")
    assert _tag_status(tmp_path, "v0.2.0", "0.2.0")[0] == "blocked"
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


def test_workflow_presence_does_not_prove_publication(tmp_path: Path):
    import shutil

    paused = tmp_path / ".github/workflows-disabled"
    paused.mkdir(parents=True)
    (tmp_path / "docs").mkdir()
    shutil.copy2(".github/workflows-disabled/release.yml", paused / "release.yml")
    shutil.copy2("docs/RELEASE_POLICY.md", tmp_path / "docs/RELEASE_POLICY.md")
    assert _release_evidence_status(tmp_path)[0] == "blocked"
    active = tmp_path / ".github/workflows"
    active.mkdir()
    (paused / "release.yml").rename(active / "release.yml")
    assert _release_evidence_status(tmp_path)[0] == "unverified"


def test_claim_manifest_does_not_accept_a_publication_claim_or_missing_source(tmp_path: Path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "source.py").write_text("")
    manifest = {
        "schema_version": "1",
        "next_release": "0.3.0",
        "claims": [
            {
                "id": "fixture",
                "claim": "Fixture",
                "introduced_in": "unreleased",
                "source": "source.py",
                "test": "source.py",
                "evidence_state": "source-present",
            }
        ],
        "external_gates": {"research": {}, "maintainer": {}, "launch": {}},
    }
    path = tmp_path / "docs/release-state.json"
    path.write_text(json.dumps(manifest))
    assert _read_release_state(tmp_path)["next_release"] == "0.3.0"
    manifest["claims"][0]["evidence_state"] = "published"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="not execution"):
        _read_release_state(tmp_path)
    manifest["claims"][0]["evidence_state"] = "source-present"
    manifest["claims"][0]["source"] = "absent.py"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="missing"):
        _read_release_state(tmp_path)
