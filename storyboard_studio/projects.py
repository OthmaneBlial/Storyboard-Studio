"""Bounded portable projects with explicit assets and no implicit file fetching."""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Literal

from pydantic import Field, field_validator

from schemas import StoryDocumentV2, StrictModel
from storyboard_studio.assets import chart_series, resolve_assets, validate_data_asset

MAX_ASSET_BYTES = 4_000_000
MAX_ARCHIVE_BYTES = 8_000_000
MAX_UNPACKED_BYTES = 12_000_000
MAX_STORY_BYTES = 200_000
RESERVED_NAMES = {
    "con",
    "prn",
    "aux",
    "nul",
    *(f"com{i}" for i in range(1, 10)),
    *(f"lpt{i}" for i in range(1, 10)),
}


def safe_project_path(value: str) -> str:
    path = PurePosixPath(value)
    if (
        not value
        or not path.parts
        or len(value) > 240
        or path.is_absolute()
        or str(path) != value
        or any(
            part in {".", ".."} or part.endswith((".", " ")) or part.split(".")[0].lower() in RESERVED_NAMES
            for part in path.parts
        )
        or any(char in value for char in '\\:\x00<>"|?*')
        or any(ord(char) < 32 for char in value)
    ):
        raise ValueError("Project paths must be canonical portable relative file paths")
    return value


class ProjectPayload(StrictModel):
    schema_version: Literal["1"] = "1"
    story: StoryDocumentV2
    files: dict[str, str] = Field(default_factory=dict, max_length=20)
    include_sources: bool = True

    @field_validator("files")
    @classmethod
    def bounded_files(cls, value: dict[str, str]) -> dict[str, str]:
        if sum(len(content) for content in value.values()) > 5_333_360:
            raise ValueError("Project assets exceed the 4 MB combined limit")
        for name in value:
            safe_project_path(name)
        return value


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def materialize_project(project: ProjectPayload, root: Path) -> StoryDocumentV2:
    """Write only declared, supplied bytes into a new private temporary directory."""
    story = project.story.model_copy(deep=True)
    assets = story.presentation.assets
    paths = [safe_project_path(asset.path) for asset in assets]
    controls = {
        "deck.story.json",
        "project.json",
        "deck.pptx",
        "deck.receipt.json",
        ".render-cache",
        "archive.zip",
    }
    if any(PurePosixPath(path).parts[0].casefold() in controls for path in paths):
        raise ValueError("Asset path conflicts with a project control file")
    if len({path.casefold() for path in paths}) != len(paths):
        raise ValueError("Asset paths must be unique, including on case-insensitive filesystems")
    if set(paths) != set(project.files):
        missing = sorted(set(paths) - set(project.files))
        raise ValueError("Supply exactly the declared asset files. Missing: " + ", ".join(missing))
    total = 0
    for asset in assets:
        try:
            content = base64.b64decode(project.files[asset.path], validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError(f"Invalid asset encoding: {asset.path}") from exc
        total += len(content)
        if total > MAX_ASSET_BYTES:
            raise ValueError("Project assets exceed the 4 MB combined limit")
        if hashlib.sha256(content).hexdigest() != asset.sha256:
            raise ValueError(f"Asset checksum mismatch: {asset.path}")
        destination = root / asset.path
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as output:
            output.write(content)
    resolved = resolve_assets(assets, root, root / ".render-cache")
    for asset in resolved.values():
        if asset.entry.kind == "data":
            validate_data_asset(asset)
    for slide in story.presentation.slides:
        block = slide.content_block
        if block and block.type == "chart":
            chart_series(resolved[block.asset_id], block)
    if not project.include_sources:
        for slide in story.presentation.slides:
            slide.sources = []
        if story.decision_brief:
            story.decision_brief.evidence = []
        story.finding_dispositions = []
        story.author_edits = []
        story.presentation.citations_appendix = False
    if len(_json_bytes(story.model_dump(mode="json"))) > MAX_STORY_BYTES:
        raise ValueError("Project story exceeds the 200 KB limit")
    return story


def project_from_files(story: StoryDocumentV2, root: Path, *, include_sources: bool = True) -> ProjectPayload:
    files = {}
    total = 0
    for asset in story.presentation.assets:
        safe_project_path(asset.path)
        source = root / asset.path
        current = root
        for part in PurePosixPath(asset.path).parts:
            current /= part
            if current.is_symlink():
                raise ValueError(f"Project assets cannot be symlinks: {asset.path}")
        if not source.is_file():
            raise ValueError(f"Missing project asset: {asset.path}")
        with source.open("rb") as stream:
            content = stream.read(MAX_ASSET_BYTES - total + 1)
        total += len(content)
        if total > MAX_ASSET_BYTES:
            raise ValueError("Project assets exceed the 4 MB combined limit")
        files[asset.path] = base64.b64encode(content).decode("ascii")
    return ProjectPayload(story=story, files=files, include_sources=include_sources)


def write_project(project: ProjectPayload, destination: Path, *, render: bool = False) -> None:
    """Create a project ZIP atomically; never replace an existing output."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="storyboard-project-", dir=destination.parent) as temporary:
        root = Path(temporary)
        story = materialize_project(project, root)
        story_path = root / "deck.story.json"
        story_path.write_bytes(_json_bytes(story.model_dump(mode="json")))
        names = ["deck.story.json", *[asset.path for asset in story.presentation.assets]]
        if render:
            from generate_pptx import create_presentation
            from storyboard_studio import __version__
            from storyboard_studio.receipt import create_receipt, digest_value

            pptx_path = root / "deck.pptx"
            create_presentation(
                story.presentation.model_dump(),
                pptx_path,
                asset_root=root,
                provenance=(
                    f"Storyboard Studio {__version__}; outline sha256 "
                    f"{digest_value(story.presentation.model_dump(mode='json'))}; "
                    "integrity does not prove factual truth."
                ),
            )
            (root / "deck.receipt.json").write_bytes(
                _json_bytes(create_receipt(story, story_path, pptx_path))
            )
            names.extend(["deck.pptx", "deck.receipt.json"])
        manifest = {
            "schema_version": "1",
            "story": "deck.story.json",
            "sources_included": project.include_sources,
            "files": {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in names},
            "external_references": sorted(
                {
                    source.local_reference
                    for slide in story.presentation.slides
                    for source in slide.sources
                    if source.local_reference
                }
            ),
            "disclaimer": (
                "Integrity only. External evidence references are not fetched or embedded. "
                "Asset data can remain sensitive even without sources."
            ),
        }
        (root / "project.json").write_bytes(_json_bytes(manifest))
        temporary_zip = root / "archive.zip"
        with zipfile.ZipFile(temporary_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name in [*names, "project.json"]:
                archive.write(root / name, name)
        if temporary_zip.stat().st_size > MAX_ARCHIVE_BYTES:
            raise ValueError("Project ZIP exceeds the 8 MB limit")
        # Same-filesystem hard link publishes the complete file without replacing anything.
        os.link(temporary_zip, destination)


def _read_project(archive_path: Path) -> ProjectPayload:
    """Inspect bounded ZIP members, hashes and asset formats without unsafe extraction."""
    if archive_path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("Project ZIP exceeds the 8 MB limit")
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        if len(members) > 24 or sum(member.file_size for member in members) > MAX_UNPACKED_BYTES:
            raise ValueError("Project ZIP has too many entries or expands beyond 12 MB")
        names = [safe_project_path(member.filename) for member in members]
        if len(set(name.casefold() for name in names)) != len(names):
            raise ValueError("Project ZIP has duplicate or case-colliding members")
        for member in members:
            mode = member.external_attr >> 16
            if (
                member.is_dir()
                or stat.S_ISLNK(mode)
                or (stat.S_IFMT(mode) not in {0, stat.S_IFREG})
                or member.flag_bits & 1
            ):
                raise ValueError("Project ZIP accepts regular unencrypted files only")
        if "project.json" not in names or archive.getinfo("project.json").file_size > MAX_STORY_BYTES:
            raise ValueError("Missing or oversized project manifest")
        manifest = json.loads(archive.read("project.json"))
        if (
            not isinstance(manifest, dict)
            or manifest.get("schema_version") != "1"
            or manifest.get("story") != "deck.story.json"
        ):
            raise ValueError("Unsupported project manifest")
        hashes = manifest.get("files")
        if not isinstance(hashes, dict) or set(hashes) != set(names) - {"project.json"}:
            raise ValueError("Project manifest does not match archive members")
        if "deck.story.json" not in hashes or archive.getinfo("deck.story.json").file_size > MAX_STORY_BYTES:
            raise ValueError("Missing or oversized project story")
        payloads = {}
        for name, digest in hashes.items():
            data = archive.read(name)
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError(f"Project checksum mismatch: {name}")
            payloads[name] = data
        story = StoryDocumentV2.model_validate_json(payloads["deck.story.json"])
        asset_paths = {asset.path for asset in story.presentation.assets}
        if set(payloads) - asset_paths - {"deck.story.json", "deck.pptx", "deck.receipt.json"}:
            raise ValueError("Project contains undeclared asset files")
        if not asset_paths.issubset(payloads):
            raise ValueError("Project is missing declared assets")
        project = ProjectPayload(
            story=story,
            files={name: base64.b64encode(payloads[name]).decode("ascii") for name in asset_paths},
        )
    with tempfile.TemporaryDirectory(prefix="storyboard-project-check-") as temporary:
        materialize_project(project, Path(temporary))
    return project


def read_project(archive_path: Path) -> ProjectPayload:
    try:
        return _read_project(archive_path)
    except (zipfile.BadZipFile, RuntimeError, KeyError, UnicodeError, RecursionError) as exc:
        raise ValueError("Invalid project archive; no files were imported") from exc


def unpack_project(archive: Path, destination: Path) -> Path:
    project = read_project(archive)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        raise ValueError("Choose a new project directory; existing files are never overwritten")
    with tempfile.TemporaryDirectory(prefix="storyboard-unpack-", dir=destination.parent) as temporary:
        root = Path(temporary)
        story = materialize_project(project, root)
        (root / "deck.story.json").write_bytes(_json_bytes(story.model_dump(mode="json")))
        shutil.rmtree(root / ".render-cache", ignore_errors=True)
        destination.mkdir()  # Exclusive; never replace an existing directory.
        try:
            shutil.copytree(root, destination, dirs_exist_ok=True)
        except OSError:
            shutil.rmtree(destination)
            raise
    return destination / "deck.story.json"
