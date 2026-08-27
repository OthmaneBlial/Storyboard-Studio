"""Installable Storyboard Studio application package."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("storyboard-studio")
except PackageNotFoundError:  # pragma: no cover - source checkout before installation
    __version__ = "0.2.0"

__all__ = ["__version__"]
