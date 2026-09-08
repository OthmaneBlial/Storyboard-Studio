import os
from concurrent.futures import ThreadPoolExecutor

import pytest

from storyboard_studio.export_store import ExportStore


def test_cleanup_preserves_foreign_files_and_expires_only_owned_exports(tmp_path, monkeypatch):
    store = ExportStore(tmp_path / "nested" / "exports")
    monkeypatch.setattr("storyboard_studio.export_store.time.time", lambda: 1000)
    identifier, path = store.create(".pptx", lambda p: p.write_bytes(b"owned"))
    foreign = store.root / "user.pptx"
    foreign.write_bytes(b"private")
    os.utime(foreign, (0, 0))
    assert store.get(identifier, ".pptx") == path
    monkeypatch.setattr("storyboard_studio.export_store.time.time", lambda: 1000 + store.ttl)
    assert store.get(identifier, ".pptx") is None
    store.cleanup()
    assert foreign.read_bytes() == b"private"
    assert not path.exists()


def test_restarted_store_reads_ownership_but_never_follows_links(tmp_path):
    store = ExportStore(tmp_path / "exports")
    identifier, path = store.create(".zip", lambda p: p.write_bytes(b"zip"))
    assert ExportStore(store.root).get(identifier, ".zip") == path
    target = tmp_path / "private.zip"
    target.write_bytes(b"private")
    path.unlink()
    path.symlink_to(target)
    assert store.get(identifier, ".zip") is None
    assert store.get("../private", ".zip") is None
    assert store.get(identifier, ".pptx") is None
    assert target.read_bytes() == b"private"


def test_failed_and_concurrent_writes_are_isolated(tmp_path):
    store = ExportStore(tmp_path)

    def fail(path):
        path.write_bytes(b"partial")
        raise OSError("simulated disk full")

    with pytest.raises(OSError, match="disk full"):
        store.create(".pptx", fail)
    assert list(tmp_path.iterdir()) == []
    with ThreadPoolExecutor(max_workers=4) as executor:
        outputs = list(
            executor.map(lambda i: store.create(".pptx", lambda p: p.write_text(str(i))), range(8))
        )
    assert len({identifier for identifier, _ in outputs}) == 8
    assert {path.read_text() for _, path in outputs} == {str(i) for i in range(8)}


def test_foreign_files_inside_owned_folder_and_symlink_roots_are_preserved(tmp_path, monkeypatch):
    store = ExportStore(tmp_path / "exports")
    _, path = store.create(".pptx", lambda p: p.write_bytes(b"deck"))
    foreign = path.parent / "user.txt"
    foreign.write_text("keep")
    monkeypatch.setattr("storyboard_studio.export_store.time.time", lambda: 10**12)
    store.cleanup()
    assert foreign.read_text() == "keep"
    link = tmp_path / "link"
    link.symlink_to(store.root, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        ExportStore(link).prepare()
