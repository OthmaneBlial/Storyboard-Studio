import json
from pathlib import Path

import pytest

from storyboard_studio.contributions import validate_contribution


def test_canonical_template_passes_all_offline_contribution_checks(tmp_path: Path):
    report = validate_contribution(
        "examples/templates/decision-brief.contribution.json",
        tmp_path,
    )

    assert report["status"] == "valid"
    assert report["checks"]["privacy"] == {
        "status": "passed",
        "network": "none",
        "findings": [],
    }
    assert report["checks"]["license"]["value"] == "CC0-1.0"
    assert report["checks"]["schema"]["input_format"] == "presentation-v1"
    assert (tmp_path / "decision-brief.pptx").read_bytes()[:2] == b"PK"
    assert (tmp_path / "decision-brief.validation.json").is_file()


def test_contribution_rejects_high_confidence_secret_before_rendering(tmp_path: Path):
    source = json.loads(Path("examples/templates/decision-brief.json").read_text(encoding="utf-8"))
    source["slides"][0]["speaker_notes"] = "ghp_123456789012345678901234567890"
    content = tmp_path / "unsafe.json"
    content.write_text(json.dumps(source), encoding="utf-8")
    manifest = tmp_path / "unsafe.contribution.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "1",
                "id": "unsafe-fixture",
                "kind": "fixture",
                "content_path": "unsafe.json",
                "content_origin": "synthetic",
                "license": "CC0-1.0",
                "attribution": "Synthetic test fixture",
                "description": "A deliberately unsafe fixture used only by the rejection test.",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Privacy validation failed"):
        validate_contribution(manifest, tmp_path / "output")

    assert not (tmp_path / "output").exists()


def test_contribution_output_requires_explicit_known_overwrite(tmp_path: Path):
    manifest = "examples/templates/decision-brief.contribution.json"
    validate_contribution(manifest, tmp_path)

    with pytest.raises(ValueError, match="output exists"):
        validate_contribution(manifest, tmp_path)

    protected = tmp_path / "notes.txt"
    protected.write_text("keep", encoding="utf-8")
    validate_contribution(manifest, tmp_path, overwrite=True)
    assert protected.read_text(encoding="utf-8") == "keep"


def test_contribution_manifest_rejects_duplicate_keys(tmp_path: Path):
    manifest = tmp_path / "duplicate.contribution.json"
    manifest.write_text(
        '{"schema_version":"1","schema_version":"1"}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate JSON key"):
        validate_contribution(manifest, tmp_path / "output")
