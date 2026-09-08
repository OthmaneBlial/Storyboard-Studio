"""Compatibility entry point for the packaged FastAPI application.

The canonical application lives in :mod:`storyboard_studio.server`.  Replacing
this module in ``sys.modules`` keeps legacy imports and monkeypatch-based
integrations pointed at the same application state.
"""

import sys as _sys

from storyboard_studio import server as _server

_sys.modules[__name__] = _server

if __name__ == "__main__":  # pragma: no cover - manual compatibility command
    import uvicorn

    uvicorn.run(_server.app, host="127.0.0.1", port=8000, reload=True)
