"""Private, owned, expiring server exports; never sweep user output folders."""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import time
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

EXPORT_ID_RE = re.compile(r"^[a-f0-9]{32}$")
TTL_SECONDS = 24 * 60 * 60
MARKER = ".storyboard-export.json"


def default_export_root() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Caches"
    elif os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local")))
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache")))
    return base / "storyboard-studio" / "exports"


class ExportStore:
    def __init__(self, root: Path, ttl: int = TTL_SECONDS):
        self.root = root
        self.ttl = ttl

    def prepare(self) -> None:
        if self.root.is_symlink():
            raise ValueError("The server export directory cannot be a symlink.")
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def _metadata(self, directory: Path) -> dict | None:
        if not EXPORT_ID_RE.fullmatch(directory.name) or directory.is_symlink():
            return None
        marker = directory / MARKER
        if marker.is_symlink():
            return None
        try:
            with marker.open("rb") as stream:
                content = stream.read(1025)
            if len(content) > 1024:
                return None
            value = json.loads(content)
            if (
                not isinstance(value, dict)
                or value.get("owner") != "storyboard-studio-export-v1"
                or value.get("id") != directory.name
                or value.get("suffix") not in (".pptx", ".zip")
                or type(value.get("created")) not in (int, float)
            ):
                return None
            return value
        except (OSError, ValueError):
            return None

    def create(self, suffix: str, write: Callable[[Path], object]) -> tuple[str, Path]:
        if suffix not in (".pptx", ".zip"):
            raise ValueError("Unsupported export type")
        self.prepare()
        identifier = uuid4().hex
        directory = self.root / identifier
        directory.mkdir(mode=0o700)  # Exclusive ownership; a collision never replaces a directory.
        try:
            metadata = {
                "owner": "storyboard-studio-export-v1",
                "id": identifier,
                "created": time.time(),
                "suffix": suffix,
            }
            (directory / MARKER).write_text(json.dumps(metadata), encoding="utf-8")
            partial = directory / ("partial" + suffix)
            write(partial)
            if partial.is_symlink() or not partial.is_file():
                raise ValueError("Renderer did not produce a regular export file")
            destination = directory / ("deck" + suffix)
            os.replace(partial, destination)
            return identifier, destination
        except BaseException:
            # Only this newly created, exclusively owned directory is removed.
            shutil.rmtree(directory)
            raise

    def get(self, identifier: str, suffix: str) -> Path | None:
        if not EXPORT_ID_RE.fullmatch(identifier):
            return None
        directory = self.root / identifier
        metadata = self._metadata(directory)
        if metadata is None or metadata["suffix"] != suffix:
            return None
        if metadata["created"] + self.ttl <= time.time():
            return None
        destination = directory / ("deck" + suffix)
        if destination.is_symlink() or not destination.is_file():
            return None
        return destination

    def cleanup(self) -> None:
        self.prepare()
        now = time.time()
        for directory in self.root.iterdir():
            metadata = self._metadata(directory)
            if metadata is None or metadata["created"] + self.ttl > now:
                continue
            # Never touch extra user files, even in a directory with our marker.
            owned = [directory / (name + metadata["suffix"]) for name in ("deck", "partial")]
            if any(path.is_symlink() for path in owned):
                continue
            try:
                for path in owned:
                    path.unlink(missing_ok=True)
                (directory / MARKER).unlink()
                directory.rmdir()
            except OSError:
                # Foreign files or an in-progress download must not stop the service.
                continue
