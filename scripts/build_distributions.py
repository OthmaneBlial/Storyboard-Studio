"""Build reproducible wheel and source distributions for a release candidate."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import gzip
import hashlib
import io
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from collections.abc import Iterable
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_MIN_ZIP_DATE = dt.datetime(1980, 1, 1, tzinfo=dt.timezone.utc)


def _resolve_epoch(value: int | None) -> int:
    if value is not None:
        if value < 0:
            raise ValueError("Build epoch must be a non-negative Unix timestamp.")
        return value
    environment_value = os.environ.get("SOURCE_DATE_EPOCH")
    if environment_value:
        try:
            epoch = int(environment_value)
        except ValueError as exc:
            raise ValueError("SOURCE_DATE_EPOCH must be an integer Unix timestamp.") from exc
        if epoch < 0:
            raise ValueError("SOURCE_DATE_EPOCH must be a non-negative Unix timestamp.")
        return epoch
    try:
        output = subprocess.check_output(
            ["git", "show", "-s", "--format=%ct", "HEAD"],
            cwd=PROJECT_ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        epoch = int(output.strip())
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        raise ValueError("Set SOURCE_DATE_EPOCH when building outside a Git checkout.") from exc
    if epoch < 0:
        raise ValueError("Git commit timestamp must be non-negative.")
    return epoch


def _zip_datetime(epoch: int) -> tuple[int, int, int, int, int, int]:
    timestamp = max(epoch, int(_MIN_ZIP_DATE.timestamp()))
    value = dt.datetime.fromtimestamp(timestamp, tz=dt.timezone.utc)
    # ZIP stores seconds with a two-second resolution.
    return value.year, value.month, value.day, value.hour, value.minute, value.second - value.second % 2


def _normalize_wheel(source: Path, destination: Path, *, epoch: int) -> None:
    """Rewrite a wheel with stable ZIP metadata and member ordering."""

    timestamp = _zip_datetime(epoch)
    with zipfile.ZipFile(source, "r") as archive:
        members = [(info.filename, archive.read(info)) for info in archive.infolist()]
    members.sort(key=lambda item: item[0])
    with zipfile.ZipFile(
        destination,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as output:
        for name, contents in members:
            info = zipfile.ZipInfo(name, date_time=timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.internal_attr = 0
            info.extra = b""
            info.comment = b""
            output.writestr(info, contents)


def _normalized_tar_member(member: tarfile.TarInfo, *, epoch: int) -> tarfile.TarInfo:
    normalized = copy.copy(member)
    normalized.mtime = epoch
    normalized.uid = 0
    normalized.gid = 0
    normalized.uname = ""
    normalized.gname = ""
    normalized.pax_headers = {}
    return normalized


def _normalize_sdist(source: Path, destination: Path, *, epoch: int) -> None:
    """Rewrite an sdist with stable tar and gzip metadata."""

    payload = io.BytesIO()
    with (
        tarfile.open(source, "r:gz") as archive,
        tarfile.open(
            fileobj=payload,
            mode="w",
            format=tarfile.PAX_FORMAT,
        ) as output,
    ):
        members = sorted(archive.getmembers(), key=lambda member: member.name)
        for member in members:
            normalized = _normalized_tar_member(member, epoch=epoch)
            if member.isfile():
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError(f"Could not read source member {member.name!r}.")
                output.addfile(normalized, io.BytesIO(stream.read()))
            else:
                output.addfile(normalized)
    with destination.open("wb") as stream:
        with gzip.GzipFile(
            fileobj=stream,
            mode="wb",
            filename="",
            mtime=epoch,
            compresslevel=9,
        ) as compressed:
            compressed.write(payload.getvalue())


def _build_raw(output_dir: Path, *, epoch: int) -> list[Path]:
    environment = os.environ.copy()
    environment["SOURCE_DATE_EPOCH"] = str(epoch)
    subprocess.run(
        [sys.executable, "-m", "build", "--outdir", str(output_dir)],
        cwd=PROJECT_ROOT,
        env=environment,
        check=True,
    )
    artifacts = sorted(
        path
        for path in output_dir.iterdir()
        if path.is_file() and (path.suffix == ".whl" or path.name.endswith(".tar.gz"))
    )
    wheels = [path for path in artifacts if path.suffix == ".whl"]
    sdists = [path for path in artifacts if path.name.endswith(".tar.gz")]
    if len(wheels) != 1 or len(sdists) != 1:
        raise RuntimeError(
            "Expected exactly one wheel and one source distribution, got "
            f"{len(wheels)} wheel(s) and {len(sdists)} sdist(s)."
        )
    return [wheels[0], sdists[0]]


def build_distributions(output_dir: str | Path, *, epoch: int | None = None) -> dict[str, object]:
    """Build and normalize the two release artifacts.

    The epoch defaults to ``SOURCE_DATE_EPOCH`` and then to the checked-out
    commit timestamp, so repeated builds from one commit have stable bytes.
    """

    destination_dir = Path(output_dir).expanduser().resolve()
    destination_dir.mkdir(parents=True, exist_ok=True)
    resolved_epoch = _resolve_epoch(epoch)
    with tempfile.TemporaryDirectory(prefix="storyboard-build-") as temporary:
        raw_dir = Path(temporary) / "raw"
        normalized_dir = Path(temporary) / "normalized"
        raw_dir.mkdir()
        normalized_dir.mkdir()
        wheel, sdist = _build_raw(raw_dir, epoch=resolved_epoch)
        normalized_wheel = normalized_dir / wheel.name
        normalized_sdist = normalized_dir / sdist.name
        _normalize_wheel(wheel, normalized_wheel, epoch=resolved_epoch)
        _normalize_sdist(sdist, normalized_sdist, epoch=resolved_epoch)
        outputs = []
        for artifact in (normalized_wheel, normalized_sdist):
            destination = destination_dir / artifact.name
            shutil.copy2(artifact, destination)
            outputs.append(
                {
                    "name": artifact.name,
                    "path": str(destination),
                    "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                    "bytes": destination.stat().st_size,
                }
            )
    return {"epoch": resolved_epoch, "artifacts": outputs}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    parser.add_argument(
        "--epoch",
        type=int,
        help="Stable Unix timestamp (defaults to SOURCE_DATE_EPOCH or Git HEAD).",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = build_distributions(args.output_dir, epoch=args.epoch)
    print(f"Built reproducible distributions at epoch {report['epoch']}")
    for artifact in report["artifacts"]:
        print(f"{artifact['name']} {artifact['bytes']} bytes sha256={artifact['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
