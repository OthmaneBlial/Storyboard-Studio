"""Compatibility entry point for the packaged PowerPoint renderer.

New code should import from :mod:`storyboard_studio.renderer`.  The module is
kept at the repository root so existing scripts and integrations continue to
work after the package layout migration.
"""

from storyboard_studio.renderer import *  # noqa: F401,F403
