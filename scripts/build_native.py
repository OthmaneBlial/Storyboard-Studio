"""Build and smoke-test a Python-free Storyboard Studio executable."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

from storyboard_studio import __version__

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "packaging" / "storyboard-studio.spec"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(command: list[str], *, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise RuntimeError(f"Command failed ({exc.returncode}): {' '.join(command)}\n{detail}") from exc


def build_native(output_dir: Path, *, verify: bool = True) -> dict[str, object]:
    """Build one executable for the current runner and return its evidence."""

    if not SPEC.is_file():
        raise FileNotFoundError(f"Missing PyInstaller specification: {SPEC}")
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir = output_dir / "build"
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(output_dir),
        "--workpath",
        str(work_dir),
        str(SPEC),
    ]
    _run(command)

    executable_name = "storyboard-studio.exe" if platform.system() == "Windows" else "storyboard-studio"
    executable = output_dir / executable_name
    if not executable.is_file() or executable.stat().st_size == 0:
        raise RuntimeError(f"PyInstaller did not produce {executable}")

    checks: dict[str, str] = {}
    if verify:
        version = _run([str(executable), "--version"])
        expected_version = f"storyboard {__version__}"
        if version.stdout.strip() != expected_version:
            raise RuntimeError(
                f"Native version mismatch: expected {expected_version!r}, got {version.stdout.strip()!r}"
            )
        checks["version"] = version.stdout.strip()
        with tempfile.TemporaryDirectory(prefix="storyboard-native-smoke-") as temporary:
            demo_path = Path(temporary) / "demo.pptx"
            demo = _run([str(executable), "demo", "--output", str(demo_path)])
            if not demo_path.is_file() or demo_path.stat().st_size == 0:
                raise RuntimeError("Native demo smoke test did not create a PPTX")
            checks["demo"] = demo.stdout.strip().splitlines()[-1]

    evidence = {
        "schema_version": "1",
        "package": "storyboard-studio",
        "version": __version__,
        "platform": platform.system().lower(),
        "architecture": platform.machine().lower(),
        "executable": executable.name,
        "size_bytes": executable.stat().st_size,
        "sha256": _sha256(executable),
        "checks": checks,
        "verified": verify,
    }
    (output_dir / "native-build.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/native"),
        help="Directory for the executable, temporary build data and evidence.",
    )
    parser.add_argument(
        "--no-verify",
        action="store_true",
        help="Build only; skip the version and offline demo smoke tests.",
    )
    args = parser.parse_args()
    evidence = build_native(args.output_dir, verify=not args.no_verify)
    print(json.dumps(evidence, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
