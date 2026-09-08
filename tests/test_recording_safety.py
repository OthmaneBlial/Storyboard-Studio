from __future__ import annotations

import subprocess
import sys


def test_legacy_recorder_requires_explicit_office_opt_in(tmp_path) -> None:
    output = tmp_path / "should-not-be-created.mp4"
    result = subprocess.run(
        [sys.executable, "scripts/record_demo.py", "--output", str(output)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "Office viewer capture is disabled by default" in result.stderr
    assert not output.exists()
