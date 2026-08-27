"""Paths to files that must work from an installed wheel."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path


def package_root() -> Path:
    return Path(str(files("storyboard_studio")))


def web_root() -> Path:
    return package_root() / "web"


def demo_outline_path() -> Path:
    return package_root() / "data" / "decision-brief.story.json"


def benchmark_suite_path() -> Path:
    return package_root() / "data" / "decision-benchmark-v1.json"


def template_catalog_path() -> Path:
    return package_root() / "data" / "template-catalog.json"


def layout_tokens_path() -> Path:
    return package_root() / "data" / "storyboard-tokens.json"
