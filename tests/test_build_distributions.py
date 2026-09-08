from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

from scripts.build_distributions import _normalize_sdist, _normalize_wheel


def _write_wheel_fixture(
    path: Path,
    *,
    timestamp: tuple[int, int, int, int, int, int],
    reverse: bool,
) -> None:
    names = ["storyboard_studio/__init__.py", "storyboard_studio-0.2.0.dist-info/METADATA"]
    if reverse:
        names.reverse()
    with zipfile.ZipFile(path, "w") as archive:
        for name in names:
            info = zipfile.ZipInfo(name, date_time=timestamp)
            archive.writestr(info, name.encode("utf-8"))


def _write_sdist_fixture(path: Path, *, mtime: int, reverse: bool) -> None:
    members = [
        ("storyboard_studio-0.2.0/README.md", b"readme"),
        ("storyboard_studio-0.2.0/storyboard_studio/__init__.py", b"package"),
    ]
    if reverse:
        members.reverse()
    with tarfile.open(path, "w:gz") as archive:
        for name, contents in members:
            member = tarfile.TarInfo(name)
            member.size = len(contents)
            member.mtime = mtime
            member.uid = 123
            member.gid = 456
            member.uname = "builder"
            member.gname = "builders"
            archive.addfile(member, io.BytesIO(contents))


def test_normalize_wheel_removes_archive_metadata_drift(tmp_path: Path):
    first = tmp_path / "first.whl"
    second = tmp_path / "second.whl"
    _write_wheel_fixture(first, timestamp=(2024, 1, 1, 0, 0, 0), reverse=False)
    _write_wheel_fixture(second, timestamp=(2025, 2, 2, 0, 0, 0), reverse=True)

    normalized_first = tmp_path / "normalized-first.whl"
    normalized_second = tmp_path / "normalized-second.whl"
    _normalize_wheel(first, normalized_first, epoch=1_800_000_000)
    _normalize_wheel(second, normalized_second, epoch=1_800_000_000)

    assert normalized_first.read_bytes() == normalized_second.read_bytes()


def test_normalize_sdist_removes_archive_metadata_drift(tmp_path: Path):
    first = tmp_path / "first.tar.gz"
    second = tmp_path / "second.tar.gz"
    _write_sdist_fixture(first, mtime=1_700_000_000, reverse=False)
    _write_sdist_fixture(second, mtime=1_750_000_000, reverse=True)

    normalized_first = tmp_path / "normalized-first.tar.gz"
    normalized_second = tmp_path / "normalized-second.tar.gz"
    _normalize_sdist(first, normalized_first, epoch=1_800_000_000)
    _normalize_sdist(second, normalized_second, epoch=1_800_000_000)

    assert normalized_first.read_bytes() == normalized_second.read_bytes()
