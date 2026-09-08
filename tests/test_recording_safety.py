from __future__ import annotations

import pytest

from scripts.record_demo import record


def test_legacy_recorder_requires_explicit_office_opt_in(tmp_path) -> None:
    with pytest.raises(RuntimeError, match="Office viewer capture is disabled"):
        record(tmp_path / "should-not-be-created.mp4")
