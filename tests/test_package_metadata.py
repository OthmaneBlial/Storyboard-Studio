from __future__ import annotations

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 uses the declared tomli dependency
    import tomli as tomllib

from pathlib import Path


def test_package_metadata_explains_the_product_and_points_to_public_proof():
    project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))["project"]

    assert "narrative compiler" in project["description"].lower()
    assert {"local-first", "powerpoint", "privacy", "decision-deck"} <= set(project["keywords"])
    assert project["urls"]["Repository"].endswith("OthmaneBlial/Storyboard-Studio")
    assert project["urls"]["Live demo"].startswith("https://othmaneblial.github.io/")
