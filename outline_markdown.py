"""Compatibility imports for the packaged Markdown interchange module.

New code should import :mod:`storyboard_studio.markdown`; this module remains
for callers that used the historical top-level import path.
"""

from storyboard_studio import markdown as _markdown
from storyboard_studio.markdown import *  # noqa: F401,F403

__all__ = _markdown.__all__
