from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.generate_sbom import generate_sbom
from scripts.validate_release_evidence import validate_release_evidence


def _write_release_fixture(tmp_path: Path) -> tuple[Path, Path]:
    dist = tmp_path / "dist"
    evidence = tmp_path / "release-evidence"
    dist.mkdir(parents=True)
    evidence.mkdir()
    artifacts = {
        "storyboard_studio-0.2.0-py3-none-any.whl": b"wheel fixture",
        "storyboard_studio-0.2.0.tar.gz": b"source fixture",
    }
    for filename, contents in artifacts.items():
        (dist / filename).write_bytes(contents)
    manifest = "\n".join(
        f"{hashlib.sha256(contents).hexdigest()}  {filename}" for filename, contents in artifacts.items()
    )
    (evidence / "SHA256SUMS").write_text(manifest + "\n", encoding="utf-8")
    payload = {
        "pip_version": "26.2.1",
        "installed": [
            {
                "metadata": {
                    "name": "storyboard-studio",
                    "version": "0.2.0",
                    "requires_dist": ["Example-Pkg>=1"],
                },
                "installer": "pip",
                "requested": True,
            },
            {"metadata": {"name": "Example-Pkg", "version": "1.0.0", "requires_dist": []}},
        ],
    }
    sbom = generate_sbom(payload, project="storyboard-studio", version="0.2.0", source="commit-a")
    (evidence / "SBOM.cdx.json").write_text(json.dumps(sbom), encoding="utf-8")
    return dist, evidence


def test_release_evidence_validates_artifacts_manifest_and_sbom(tmp_path: Path):
    dist, evidence = _write_release_fixture(tmp_path)

    report = validate_release_evidence(
        dist,
        evidence,
        project="storyboard-studio",
        version="0.2.0",
        source="commit-a",
    )

    assert report["status"] == "valid"
    assert len(report["artifacts"]) == 2


def test_release_evidence_rejects_tampered_artifact_and_mismatched_sbom(tmp_path: Path):
    dist, evidence = _write_release_fixture(tmp_path)
    (dist / "storyboard_studio-0.2.0.tar.gz").write_bytes(b"tampered")

    with pytest.raises(ValueError, match="Checksum mismatch"):
        validate_release_evidence(
            dist,
            evidence,
            project="storyboard-studio",
            version="0.2.0",
            source="commit-a",
        )

    dist, evidence = _write_release_fixture(tmp_path / "second")
    with pytest.raises(ValueError, match="project and version"):
        validate_release_evidence(
            dist,
            evidence,
            project="storyboard-studio",
            version="0.3.0",
            source="commit-a",
        )
