"""Inspect built Python archives for required runtime data and private payloads."""

from __future__ import annotations

import argparse
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

PRIVATE_PARTS = {"output", ".venv", ".git", "research-sessions", "rushes", "__pycache__"}
REQUIRED = {
    "storyboard_studio/cli.py",
    "storyboard_studio/projects.py",
    "storyboard_studio/web/static/projects.js",
    "storyboard_studio/web/index.html",
    "storyboard_studio/web/static/app.js",
    "storyboard_studio/data/decision-brief.story.json",
    "storyboard_studio/data/storyboard-tokens.json",
}


def validate_distribution(path: Path) -> dict:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
    elif path.name.endswith(".tar.gz"):
        with tarfile.open(path, "r:gz") as archive:
            names = []
            roots = set()
            for member in archive.getmembers():
                item = PurePosixPath(member.name)
                if item.is_absolute() or ".." in item.parts or member.issym() or member.islnk():
                    raise ValueError(f"Forbidden distribution input: {member.name}")
                if not item.parts:
                    continue
                roots.add(item.parts[0])
                if member.isfile():
                    names.append(str(item.relative_to(item.parts[0])))
            if len(roots) != 1:
                raise ValueError("Source archive must have one root directory")
    else:
        raise ValueError("Expected a wheel or source tar.gz")
    for name in names:
        item = PurePosixPath(name)
        if (
            item.is_absolute()
            or ".." in item.parts
            or PRIVATE_PARTS.intersection(item.parts)
            or item.name == ".env"
            or item.name.startswith(".env.")
            or item.suffix in {".key", ".pem", ".pyc"}
        ):
            raise ValueError(f"Forbidden distribution input: {name}")
    missing = REQUIRED.difference(names)
    if missing:
        raise ValueError("Missing packaged runtime data: " + ", ".join(sorted(missing)))
    return {
        "archive": path.name,
        "members": len(names),
        "bytes": path.stat().st_size,
        "runtime_data": "present",
        "private_paths": "absent",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archives", nargs="+", type=Path)
    args = parser.parse_args()
    for path in args.archives:
        try:
            print(validate_distribution(path))
        except (OSError, ValueError, tarfile.TarError, zipfile.BadZipFile) as exc:
            parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
