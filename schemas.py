"""Compatibility imports for the packaged Storyboard Studio contracts.

New code should import contracts from :mod:`storyboard_studio.schemas`. This
module remains available for existing scripts and integrations that imported
``schemas`` before the package layout was introduced.
"""

from storyboard_studio.schemas import *  # noqa: F401,F403
