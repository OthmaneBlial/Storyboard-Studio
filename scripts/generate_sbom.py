"""Generate a deterministic CycloneDX SBOM from ``pip inspect`` JSON."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import quote

_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
_NORMALIZED_RE = re.compile(r"[-_.]+")
_PYTHON_MARKER_RE = re.compile(r"^python_version\s*(==|!=|<=|>=|<|>)\s*['\"](\d+(?:\.\d+)*)['\"]$")
_GENERATOR_VERSION = "1"


def _normalize_name(name: str) -> str:
    return _NORMALIZED_RE.sub("-", name).lower()


def _package_ref(name: str, version: str) -> str:
    normalized_name = _normalize_name(name)
    return f"pkg:pypi/{quote(normalized_name, safe='-._~')}@{quote(version, safe='-._~')}"


def _fallback_marker_active(marker: str) -> bool:
    match = _PYTHON_MARKER_RE.fullmatch(marker.strip())
    if match is None:
        return True
    operator, expected_text = match.groups()
    current = (sys.version_info.major, sys.version_info.minor)
    expected_parts = tuple(int(part) for part in expected_text.split("."))
    expected = expected_parts + (0,) * (2 - len(expected_parts))
    if operator == "==":
        return current == expected
    if operator == "!=":
        return current != expected
    if operator == "<":
        return current < expected
    if operator == "<=":
        return current <= expected
    if operator == ">":
        return current > expected
    return current >= expected


def _requirement_name(requirement: object) -> tuple[str | None, bool]:
    if not isinstance(requirement, str):
        return None, True
    try:
        from packaging.requirements import InvalidRequirement, Requirement

    except ImportError:
        marker = requirement.split(";", 1)[1] if ";" in requirement else ""
        if marker and not _fallback_marker_active(marker):
            return None, False
    else:
        try:
            parsed = Requirement(requirement)
        except InvalidRequirement:
            parsed = None
        if parsed is not None:
            if parsed.marker is not None and not parsed.marker.evaluate():
                return None, False
            return _normalize_name(parsed.name), True
    match = _NAME_RE.match(requirement)
    return (_normalize_name(match.group(1)), True) if match else (None, True)


def _load_payload(source: str | None) -> dict[str, Any]:
    if source is None:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "inspect", "--local"],
            check=True,
            capture_output=True,
            text=True,
        )
        raw = result.stdout
    else:
        raw = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"pip inspect input is not valid JSON: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("installed"), list):
        raise ValueError("pip inspect input must contain an installed list")
    return payload


def _load_project(project_file: Path) -> tuple[str, str]:
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
        import tomli as tomllib

    payload = tomllib.loads(project_file.read_text(encoding="utf-8"))
    project = payload.get("project")
    if not isinstance(project, dict) or not isinstance(project.get("name"), str):
        raise ValueError(f"{project_file} does not define project.name")
    version = project.get("version")
    if not isinstance(version, str) or not version:
        raise ValueError(f"{project_file} does not define a static project.version")
    return project["name"], version


def _record_map(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for entry in payload["installed"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("metadata"), dict):
            raise ValueError("pip inspect contains an entry without metadata")
        metadata = entry["metadata"]
        name = metadata.get("name")
        version = metadata.get("version")
        if (
            not isinstance(name, str)
            or not name.strip()
            or not isinstance(version, str)
            or not version.strip()
        ):
            raise ValueError("pip inspect metadata requires non-empty name and version")
        key = _normalize_name(name)
        if key in records:
            raise ValueError(f"pip inspect contains duplicate package {name!r}")
        records[key] = {"entry": entry, "metadata": metadata, "name": name, "version": version}
    return records


def _dependency_refs(
    requirements: object,
    records: dict[str, dict[str, Any]],
) -> tuple[list[str], list[str]]:
    references: list[str] = []
    unresolved: list[str] = []
    if not isinstance(requirements, list):
        return references, unresolved
    for requirement in requirements:
        name, active = _requirement_name(requirement)
        if not active:
            continue
        if name is None:
            unresolved.append(str(requirement))
            continue
        record = records.get(name)
        if record is None:
            unresolved.append(str(requirement))
            continue
        references.append(_package_ref(record["name"], record["version"]))
    return sorted(set(references)), unresolved


def generate_sbom(
    payload: dict[str, Any],
    *,
    project: str,
    version: str,
    source: str,
) -> dict[str, Any]:
    """Convert a pip-inspect payload into a deterministic CycloneDX document."""

    if not project.strip() or not version.strip():
        raise ValueError("project and version must be non-empty")
    records = _record_map(payload)
    root_key = _normalize_name(project)
    root_record = records.get(root_key)
    root_ref = _package_ref(project, version)
    if root_record is not None and root_record["version"] != version:
        raise ValueError(
            f"installed project version {root_record['version']!r} does not match requested {version!r}"
        )

    components: list[dict[str, Any]] = []
    component_refs: dict[str, str] = {}
    unresolved_by_ref: dict[str, list[str]] = {}
    for key in sorted(records):
        if key == root_key:
            continue
        record = records[key]
        ref = _package_ref(record["name"], record["version"])
        component_refs[key] = ref
        component: dict[str, Any] = {
            "type": "library",
            "bom-ref": ref,
            "name": record["name"],
            "version": record["version"],
            "purl": ref,
        }
        entry = record["entry"]
        properties: list[dict[str, str]] = []
        if isinstance(entry.get("installer"), str) and entry["installer"]:
            properties.append({"name": "pip:installer", "value": entry["installer"]})
        if isinstance(entry.get("requested"), bool):
            properties.append({"name": "pip:requested", "value": str(entry["requested"]).lower()})
        if properties:
            component["properties"] = properties
        components.append(component)

    dependencies: list[dict[str, Any]] = []
    root_requirements = root_record["metadata"].get("requires_dist", []) if root_record else []
    root_dependencies, root_unresolved = _dependency_refs(root_requirements, records)
    if root_unresolved:
        unresolved_by_ref[root_ref] = root_unresolved
    dependencies.append({"ref": root_ref, "dependsOn": root_dependencies})

    for key in sorted(component_refs):
        record = records[key]
        refs, unresolved = _dependency_refs(record["metadata"].get("requires_dist", []), records)
        refs = [ref for ref in refs if ref in component_refs.values() or ref == root_ref]
        if unresolved:
            unresolved_by_ref[component_refs[key]] = unresolved
        dependencies.append({"ref": component_refs[key], "dependsOn": refs})

    if root_unresolved:
        root_properties = [
            {"name": "sbom:unresolved-requirement", "value": value} for value in root_unresolved
        ]
        root_component = {
            "type": "application",
            "bom-ref": root_ref,
            "name": project,
            "version": version,
            "purl": root_ref,
            "properties": root_properties,
        }
    else:
        root_component = {
            "type": "application",
            "bom-ref": root_ref,
            "name": project,
            "version": version,
            "purl": root_ref,
        }

    for dependency in dependencies:
        unresolved = unresolved_by_ref.get(dependency["ref"])
        if not unresolved:
            continue
        target = next(
            (component for component in components if component["bom-ref"] == dependency["ref"]), None
        )
        if target is not None:
            target["properties"] = target.get("properties", []) + [
                {"name": "sbom:unresolved-requirement", "value": value} for value in unresolved
            ]

    material = {
        "project": project,
        "version": version,
        "source": source,
        "pip_version": payload.get("pip_version", "unknown"),
        "components": components,
        "dependencies": dependencies,
    }
    digest = hashlib.sha256(
        json.dumps(material, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    serial = f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, digest)}"
    metadata_properties = [
        {"name": "sbom:source", "value": source},
        {"name": "sbom:pip-version", "value": str(payload.get("pip_version", "unknown"))},
    ]
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": serial,
        "version": 1,
        "metadata": {
            "component": root_component,
            "properties": metadata_properties,
            "tools": [
                {"vendor": "Storyboard Studio", "name": "generate_sbom.py", "version": _GENERATOR_VERSION}
            ],
        },
        "components": components,
        "dependencies": dependencies,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", help="pip inspect JSON path, '-' for stdin, or omit to inspect the current environment"
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--project")
    parser.add_argument("--version")
    parser.add_argument(
        "--project-file", type=Path, help="pyproject.toml used when project/version are omitted"
    )
    parser.add_argument("--source", default="working-tree")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    project, version = args.project, args.version
    if (project is None or version is None) and args.project_file is None:
        raise SystemExit("--project and --version are required unless --project-file is supplied")
    if args.project_file is not None:
        file_project, file_version = _load_project(args.project_file)
        project = project or file_project
        version = version or file_version
    assert project is not None and version is not None
    document = generate_sbom(
        _load_payload(args.input),
        project=project,
        version=version,
        source=args.source,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Created {args.output} with {len(document['components'])} component(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
