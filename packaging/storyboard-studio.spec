# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification for the Python-free Storyboard Studio launcher."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all


# PyInstaller executes a spec as a small Python program without defining
# ``__file__``. The supported builder invokes it from the repository root.
ROOT = Path.cwd().resolve()

storyboard_datas, storyboard_binaries, storyboard_hiddenimports = collect_all(
    "storyboard_studio", include_py_files=False
)
pptx_datas, pptx_binaries, pptx_hiddenimports = collect_all("pptx", include_py_files=False)

datas = storyboard_datas + pptx_datas
# python-pptx resolves templates from ``pptx/oxml/../templates`` using the
# module's ``__file__`` path. Its Python modules live in the PyInstaller
# archive, so keep the on-disk parent directory present without embedding raw
# application or dependency source files.
datas.append((str(ROOT / "packaging" / "pptx-oxml-placeholder.txt"), "pptx/oxml"))
binaries = storyboard_binaries + pptx_binaries
hiddenimports = storyboard_hiddenimports + pptx_hiddenimports


a = Analysis(
    [str(ROOT / "storyboard_studio" / "cli.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="storyboard-studio",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
