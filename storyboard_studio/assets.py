"""Strict local asset resolution for charts and presentation images."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cairosvg
from PIL import Image, UnidentifiedImageError

from schemas import ChartBlock, LocalAsset

MAX_DATA_BYTES = 256_000
MAX_IMAGE_BYTES = 5_000_000
MAX_IMAGE_PIXELS = 20_000_000
MAX_CHART_ROWS = 12
MAX_DATA_COLUMNS = 8
MEDIA_EXTENSIONS = {
    "text/csv": {".csv"},
    "application/json": {".json"},
    "image/png": {".png"},
    "image/jpeg": {".jpg", ".jpeg"},
    "image/svg+xml": {".svg"},
}


class AssetValidationError(ValueError):
    """An asset is unsafe, missing, or inconsistent with its manifest entry."""


@dataclass(frozen=True)
class ResolvedAsset:
    entry: LocalAsset
    source_path: Path
    render_path: Path
    width: int | None = None
    height: int | None = None


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_svg(source: Path, cache_dir: Path, asset: LocalAsset) -> tuple[Path, int, int]:
    content = source.read_bytes()
    lowered = content.lower()
    if b"<!doctype" in lowered or b"<!entity" in lowered or b"url(" in lowered:
        raise AssetValidationError(
            f"SVG asset {asset.id!r} contains a DTD, entity, or URL reference. "
            "Remove external references and try again."
        )
    try:
        root = ET.fromstring(content)
    except ET.ParseError as exc:
        raise AssetValidationError(f"SVG asset {asset.id!r} is not well-formed XML: {exc}.") from exc
    forbidden = {"script", "foreignobject", "animate", "animatemotion", "animatetransform", "set"}
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1].lower()
        if tag in forbidden:
            raise AssetValidationError(f"SVG asset {asset.id!r} contains unsupported active element <{tag}>.")
        for name, value in element.attrib.items():
            attribute = name.rsplit("}", 1)[-1].lower()
            if attribute == "href" and value and not value.startswith("#"):
                raise AssetValidationError(
                    f"SVG asset {asset.id!r} contains a non-local href. Embed the artwork locally."
                )
    cache_dir.mkdir(parents=True, exist_ok=True)
    destination = cache_dir / f"{asset.id}.png"
    try:
        cairosvg.svg2png(bytestring=content, write_to=str(destination), output_width=1600)
    except (OSError, ValueError) as exc:
        raise AssetValidationError(f"SVG asset {asset.id!r} could not be rendered safely: {exc}.") from exc
    with Image.open(destination) as image:
        return destination, image.width, image.height


def _raster_dimensions(source: Path, asset: LocalAsset) -> tuple[int, int]:
    try:
        with Image.open(source) as image:
            image.verify()
        with Image.open(source) as image:
            width, height = image.size
    except (OSError, UnidentifiedImageError) as exc:
        raise AssetValidationError(
            f"Image asset {asset.id!r} is unreadable. Replace it with a valid PNG or JPEG."
        ) from exc
    if width <= 0 or height <= 0 or width * height > MAX_IMAGE_PIXELS:
        raise AssetValidationError(
            f"Image asset {asset.id!r} is oversized ({width}x{height}). Keep images below 20 megapixels."
        )
    return width, height


def resolve_assets(
    assets: list[LocalAsset],
    root: Path,
    cache_dir: Path,
) -> dict[str, ResolvedAsset]:
    """Verify local paths, hashes, media types, sizes, and safe image decoding."""
    base = root.expanduser().resolve()
    resolved: dict[str, ResolvedAsset] = {}
    for asset in assets:
        source = (base / asset.path).resolve()
        try:
            source.relative_to(base)
        except ValueError as exc:
            raise AssetValidationError(
                f"Asset {asset.id!r} escapes the allowed root. Use a local relative path."
            ) from exc
        if not source.is_file():
            raise AssetValidationError(
                f"Asset {asset.id!r} is missing at {asset.path!r}. Restore the file or update the manifest."
            )
        if source.suffix.lower() not in MEDIA_EXTENSIONS[asset.media_type]:
            raise AssetValidationError(f"Asset {asset.id!r} extension does not match {asset.media_type}.")
        limit = MAX_IMAGE_BYTES if asset.kind == "image" else MAX_DATA_BYTES
        size = source.stat().st_size
        if size > limit:
            raise AssetValidationError(f"Asset {asset.id!r} is oversized ({size} bytes; limit {limit}).")
        actual = _digest(source)
        if actual != asset.sha256:
            raise AssetValidationError(
                f"Asset {asset.id!r} checksum mismatch. Expected {asset.sha256}, got {actual}."
            )
        render_path = source
        width = height = None
        if asset.media_type == "image/svg+xml":
            render_path, width, height = _safe_svg(source, cache_dir, asset)
        elif asset.kind == "image":
            width, height = _raster_dimensions(source, asset)
        resolved[asset.id] = ResolvedAsset(asset, source, render_path, width, height)
    return resolved


def _load_rows(asset: ResolvedAsset) -> list[dict[str, Any]]:
    if asset.entry.media_type == "text/csv":
        with asset.source_path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file)
            if not reader.fieldnames:
                raise AssetValidationError(f"Data asset {asset.entry.id!r} has no header row.")
            if len(reader.fieldnames) > MAX_DATA_COLUMNS:
                raise AssetValidationError(
                    f"Data asset {asset.entry.id!r} has too many columns; keep at most {MAX_DATA_COLUMNS}."
                )
            rows = list(reader)
    else:
        try:
            payload = json.loads(asset.source_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AssetValidationError(
                f"Data asset {asset.entry.id!r} contains invalid JSON: {exc.msg}."
            ) from exc
        rows = payload.get("rows") if isinstance(payload, Mapping) else payload
        if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
            raise AssetValidationError(
                f"Data asset {asset.entry.id!r} must be a JSON row array or an object with a rows array."
            )
        rows = [dict(row) for row in rows]
        columns = {str(key) for row in rows for key in row}
        if len(columns) > MAX_DATA_COLUMNS:
            raise AssetValidationError(
                f"Data asset {asset.entry.id!r} has too many columns; keep at most {MAX_DATA_COLUMNS}."
            )
    if not 1 <= len(rows) <= MAX_CHART_ROWS:
        raise AssetValidationError(
            f"Data asset {asset.entry.id!r} must contain 1–{MAX_CHART_ROWS} rows for a chart."
        )
    return [dict(row) for row in rows]


def validate_data_asset(asset: ResolvedAsset) -> None:
    """Validate a manifest data file even before a chart selects its fields."""
    _load_rows(asset)


def chart_series(
    asset: ResolvedAsset,
    block: ChartBlock,
) -> tuple[list[str], list[tuple[str, list[float]]]]:
    """Return bounded native-chart categories and numeric series."""
    rows = _load_rows(asset)
    required = [block.category_field, *block.value_fields]
    missing = [field for field in required if any(field not in row for row in rows)]
    if missing:
        raise AssetValidationError(
            f"Chart asset {asset.entry.id!r} is missing fields: {', '.join(sorted(set(missing)))}."
        )
    categories = [str(row[block.category_field]).strip() for row in rows]
    if any(not category or len(category) > 60 for category in categories):
        raise AssetValidationError(f"Chart asset {asset.entry.id!r} has an empty or overlong category label.")
    series: list[tuple[str, list[float]]] = []
    for field in block.value_fields:
        values: list[float] = []
        for row in rows:
            try:
                value = float(row[field])
            except (TypeError, ValueError) as exc:
                raise AssetValidationError(
                    f"Chart field {field!r} in asset {asset.entry.id!r} must contain only numbers."
                ) from exc
            if not math.isfinite(value):
                raise AssetValidationError(
                    f"Chart field {field!r} in asset {asset.entry.id!r} contains a non-finite number."
                )
            values.append(value)
        series.append((field, values))
    if block.chart_type == "donut" and len(series) != 1:
        raise AssetValidationError("Donut charts require exactly one value field.")
    return categories, series
