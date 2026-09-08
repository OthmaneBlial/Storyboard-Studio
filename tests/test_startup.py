import socket

import pytest

from storyboard_studio.cli import main
from storyboard_studio.startup import check_startup


def test_occupied_port_has_actionable_error(tmp_path):
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        with pytest.raises(ValueError, match="--port 8001"):
            check_startup("127.0.0.1", listener.getsockname()[1], tmp_path / "cache")


def test_invalid_cache_has_actionable_error(tmp_path):
    cache = tmp_path / "file"
    cache.write_text("user data")
    with pytest.raises(ValueError, match="STORYBOARD_OUTPUT_DIR"):
        check_startup("127.0.0.1", 8000, cache)
    assert cache.read_text() == "user data"


def test_invalid_port_returns_cli_error_without_traceback(capsys):
    assert main(["serve", "--port", "70000"]) == 2
    assert "between 1 and 65535" in capsys.readouterr().err
