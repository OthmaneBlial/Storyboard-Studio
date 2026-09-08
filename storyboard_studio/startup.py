"""Actionable checks for the installed local server."""

from __future__ import annotations

import socket
import tempfile
from pathlib import Path

from storyboard_studio.export_store import ExportStore


def check_startup(host: str, port: int, cache_root: Path) -> None:
    if not 1 <= port <= 65535:
        raise ValueError("Choose a port between 1 and 65535 with --port.")
    try:
        ExportStore(cache_root, 86400).prepare()
        with tempfile.TemporaryFile(dir=cache_root) as probe:
            probe.write(b"startup check")
    except OSError as exc:
        raise ValueError(
            "The export cache is not writable. Set STORYBOARD_OUTPUT_DIR to a writable private directory."
        ) from exc
    try:
        family = socket.AF_INET6 if ":" in host else socket.AF_INET
        with socket.socket(family, socket.SOCK_STREAM) as probe:
            probe.bind((host, port))
    except OSError as exc:
        raise ValueError(
            f"Cannot listen on {host}:{port}. Check --host or choose a free port, for example --port 8001."
        ) from exc
