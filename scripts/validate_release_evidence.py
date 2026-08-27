"""Validate release checksums and CycloneDX evidence against built artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

_SHA256_LINE = re.compile(r"^([0-9a-fA-F]{64})  (.+)$")
_SAFE_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")
_UUID_SERIAL = re.compile(r"^urn:uuid:[0-9a-f-]{36}$")
_NORMALIZED_NAME = re.compile(r"[-_.]+")


def _normalize_name(value: str) -> str:
    return _NORMALIZED_NAME.sub("-", value).lower()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_manifest(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"Could not read checksum manifest {path}: {exc}") from exc
    if not lines:
        raise ValueError("Checksum manifest is empty.")
    entries: dict[str, str] = {}
    for line_number, line in enumerate(lines, start=1):
        match = _SHA256_LINE.fullmatch(line)
        if match is None:
            raise ValueError(f"Checksum manifest line {line_number} is not '<sha256>  <filename>'.")
        digest, filename = match.groups()
        if not _SAFE_FILENAME.fullmatch(filename):
            raise ValueError(f"Checksum manifest filename {filename!r} is not a safe artifact name.")
        if filename in entries:
            raise ValueError(f"Checksum manifest contains duplicate artifact {filename!r}.")
        entries[filename] = digest.lower()
    return entries


def _validate_sbom(path: Path, *, project: str, version: str, source: str | None) -> None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"SBOM is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("SBOM must be a JSON object.")
    if payload.get("bomFormat") != "CycloneDX" or payload.get("specVersion") != "1.5":
        raise ValueError("SBOM must use CycloneDX specVersion 1.5.")
    serial = payload.get("serialNumber")
    if not isinstance(serial, str) or _UUID_SERIAL.fullmatch(serial) is None:
        raise ValueError("SBOM serialNumber must be a UUID URN.")
    metadata = payload.get("metadata")
    root = metadata.get("component") if isinstance(metadata, dict) else None
    expected_ref = f"pkg:pypi/{_normalize_name(project)}@{version}"
    if (
        not isinstance(root, dict)
        or root.get("name") != project
        or root.get("version") != version
        or root.get("bom-ref") != expected_ref
        or root.get("purl") != expected_ref
    ):
        raise ValueError("SBOM metadata component does not match the release project and version.")
    properties = metadata.get("properties", []) if isinstance(metadata, dict) else []
    if source is not None and not any(
        isinstance(item, dict) and item.get("name") == "sbom:source" and item.get("value") == source
        for item in properties
    ):
        raise ValueError("SBOM source property does not match the release source.")
    components = payload.get("components")
    dependencies = payload.get("dependencies")
    if not isinstance(components, list) or not components:
        raise ValueError("SBOM must contain at least one dependency component.")
    if not isinstance(dependencies, list):
        raise ValueError("SBOM dependencies must be a list.")
    refs = [item.get("bom-ref") for item in components if isinstance(item, dict)]
    if (
        len(refs) != len(components)
        or len(set(refs)) != len(refs)
        or any(not isinstance(ref, str) for ref in refs)
    ):
        raise ValueError("SBOM components must have unique bom-ref values.")
    dependency_refs = [item.get("ref") for item in dependencies if isinstance(item, dict)]
    if (
        len(dependency_refs) != len(set(dependency_refs))
        or expected_ref not in dependency_refs
        or set(dependency_refs) != {expected_ref, *refs}
    ):
        raise ValueError("SBOM dependency graph does not cover the project and every component.")


def validate_release_evidence(
    dist_dir: str | Path,
    evidence_dir: str | Path,
    *,
    project: str,
    version: str,
    source: str | None = None,
) -> dict[str, Any]:
    """Verify release artifacts, checksums, and SBOM identity."""

    dist = Path(dist_dir).expanduser().resolve()
    evidence = Path(evidence_dir).expanduser().resolve()
    if not dist.is_dir():
        raise ValueError(f"Distribution directory does not exist: {dist}")
    artifact_paths = sorted(path for path in dist.iterdir() if path.is_file())
    if not artifact_paths:
        raise ValueError("Distribution directory contains no files.")
    if not any(path.name.endswith(".whl") for path in artifact_paths):
        raise ValueError("Distribution directory must contain a wheel.")
    if not any(path.name.endswith(".tar.gz") for path in artifact_paths):
        raise ValueError("Distribution directory must contain a source distribution.")
    manifest = _read_manifest(evidence / "SHA256SUMS")
    artifact_names = {path.name for path in artifact_paths}
    if set(manifest) != artifact_names:
        missing = sorted(artifact_names - set(manifest))
        extra = sorted(set(manifest) - artifact_names)
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("unknown " + ", ".join(extra))
        raise ValueError("Checksum manifest does not match dist/: " + "; ".join(details))
    for path in artifact_paths:
        actual = _sha256(path)
        if actual != manifest[path.name]:
            raise ValueError(f"Checksum mismatch for {path.name}.")
    sbom_path = evidence / "SBOM.cdx.json"
    if not sbom_path.is_file():
        raise ValueError(f"SBOM evidence is missing: {sbom_path}")
    _validate_sbom(sbom_path, project=project, version=version, source=source)
    return {
        "status": "valid",
        "artifacts": [path.name for path in artifact_paths],
        "checksum_manifest": "SHA256SUMS",
        "sbom": "SBOM.cdx.json",
        "project": project,
        "version": version,
        "source": source,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist-dir", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--source")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = validate_release_evidence(
        args.dist_dir,
        args.evidence_dir,
        project=args.project,
        version=args.version,
        source=args.source,
    )
    print(
        f"Release evidence valid: {len(report['artifacts'])} artifact(s), "
        f"{report['project']} {report['version']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
