from __future__ import annotations

import pytest

from scripts.generate_sbom import generate_sbom


def _inspect_payload() -> dict:
    return {
        "version": "1",
        "pip_version": "26.2.1",
        "installed": [
            {
                "metadata": {
                    "name": "storyboard-studio",
                    "version": "0.2.0",
                    "requires_dist": [
                        "Example_Pkg>=1",
                        "missing-lib>=1",
                        "old-lib; python_version < '3.11'",
                    ],
                },
                "installer": "pip",
                "requested": True,
            },
            {
                "metadata": {
                    "name": "Example_Pkg",
                    "version": "1.2.3",
                    "requires_dist": ["nested>=2"],
                },
                "installer": "pip",
                "requested": False,
            },
            {
                "metadata": {"name": "nested", "version": "2.0.0", "requires_dist": []},
                "installer": "pip",
                "requested": False,
            },
        ],
    }


def test_sbom_is_deterministic_and_preserves_dependency_graph():
    payload = _inspect_payload()
    first = generate_sbom(payload, project="storyboard-studio", version="0.2.0", source="test")
    second = generate_sbom(payload, project="storyboard-studio", version="0.2.0", source="test")

    assert first == second
    assert first["bomFormat"] == "CycloneDX"
    assert first["specVersion"] == "1.5"
    assert first["metadata"]["component"]["purl"] == "pkg:pypi/storyboard-studio@0.2.0"
    assert [component["name"] for component in first["components"]] == ["Example_Pkg", "nested"]

    root_ref = first["metadata"]["component"]["bom-ref"]
    example_ref = next(
        component["bom-ref"] for component in first["components"] if component["name"] == "Example_Pkg"
    )
    nested_ref = next(
        component["bom-ref"] for component in first["components"] if component["name"] == "nested"
    )
    dependencies = {item["ref"]: item["dependsOn"] for item in first["dependencies"]}
    assert dependencies[root_ref] == [example_ref]
    assert dependencies[example_ref] == [nested_ref]
    assert any(
        prop["name"] == "sbom:unresolved-requirement" and prop["value"] == "missing-lib>=1"
        for prop in first["metadata"]["component"]["properties"]
    )
    assert all(
        prop["value"] != "old-lib; python_version < '3.11'"
        for prop in first["metadata"]["component"]["properties"]
    )


def test_sbom_serial_changes_when_source_changes():
    payload = _inspect_payload()
    first = generate_sbom(payload, project="storyboard-studio", version="0.2.0", source="commit-a")
    second = generate_sbom(payload, project="storyboard-studio", version="0.2.0", source="commit-b")

    assert first["serialNumber"] != second["serialNumber"]


def test_sbom_rejects_duplicate_or_mismatched_project_records():
    payload = _inspect_payload()
    payload["installed"].append({"metadata": {"name": "example-pkg", "version": "9.9.9"}})
    with pytest.raises(ValueError, match="duplicate package"):
        generate_sbom(payload, project="storyboard-studio", version="0.2.0", source="test")

    with pytest.raises(ValueError, match="does not match"):
        generate_sbom(_inspect_payload(), project="storyboard-studio", version="9.9.9", source="test")
