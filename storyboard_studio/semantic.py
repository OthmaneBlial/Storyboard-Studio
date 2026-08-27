"""Semantic block normalization and accessible plain-text fallbacks."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _text(value: Any, fallback: str = "") -> str:
    return " ".join(value.split()) if isinstance(value, str) and value.strip() else fallback


def _legacy_points(slide: Mapping[str, Any]) -> list[dict[str, str]]:
    raw = slide.get("bullet_points")
    points = raw if isinstance(raw, list) else []
    return [
        {
            "label": _text(point.get("label"), str(index).zfill(2)),
            "title": _text(point.get("title"), f"Point {index}"),
            "description": _text(point.get("description"), "No description supplied."),
        }
        for index, point in enumerate(points[:3], start=1)
        if isinstance(point, Mapping)
    ]


def normalize_content_block(slide: Mapping[str, Any]) -> dict[str, Any]:
    """Return a typed block, adapting a validated legacy three-point slide when needed."""
    current = slide.get("content_block")
    if isinstance(current, Mapping) and isinstance(current.get("type"), str):
        return dict(current)

    points = _legacy_points(slide)
    block = _text(slide.get("block"), "standard")
    content = _text(slide.get("content"), "No summary supplied.")
    sources = slide.get("sources") if isinstance(slide.get("sources"), list) else []
    source = sources[0] if sources and isinstance(sources[0], Mapping) else {}
    owner = _text(source.get("owner"))

    if block == "comparison":
        return {
            "type": "comparison",
            "sides": [{"title": point["title"], "summary": point["description"]} for point in points[:2]],
            "criteria": [
                {
                    "label": points[2]["title"] if len(points) > 2 else "Comparison",
                    "left": points[0]["description"],
                    "right": points[1]["description"],
                }
            ],
        }
    if block == "decision":
        return {
            "type": "decision",
            "decision": content,
            "options": [
                {"title": point["title"], "description": point["description"]} for point in points[:3]
            ],
            "rationale": points[-1]["description"],
            "owner": owner,
        }
    if block == "timeline":
        return {
            "type": "timeline",
            "steps": [
                {
                    "label": point["label"],
                    "title": f"{point['title']}: {point['description']}",
                    "owner": owner,
                }
                for point in points
            ],
        }
    if block == "metric":
        return {
            "type": "metric",
            "value": points[0]["label"],
            "label": points[0]["title"],
            "context": points[0]["description"],
            "source": _text(source.get("label")),
        }
    if block == "process":
        return {
            "type": "process",
            "steps": [{"title": point["title"], "description": point["description"]} for point in points],
        }
    if block == "quote":
        return {
            "type": "quote",
            "quote": content,
            "attribution": points[0]["title"],
            "evidence": points[0]["description"],
        }
    if block == "table":
        return {
            "type": "table",
            "columns": ["Point", "Detail"],
            "rows": [{"cells": [point["title"], point["description"]]} for point in points],
            "accessible_summary": content,
        }
    if block == "chart":
        return {
            "type": "chart",
            "chart_type": "bar",
            "asset_id": "local-data",
            "category_field": "category",
            "value_fields": ["value"],
            "title": _text(slide.get("title"), "Local chart"),
            "source_note": "Add a checksum-verified local CSV or JSON source.",
        }
    if block == "image":
        return {
            "type": "image",
            "asset_id": "local-image",
            "alt_text": content,
            "caption": "",
            "fit": "contain",
        }
    return {"type": "standard", "points": points}


def block_plain_text(block: Mapping[str, Any]) -> str:
    """Return stable accessible text for preview, diagnostics, and text export."""
    kind = block.get("type")
    parts: list[str] = []
    if kind == "standard":
        for point in block.get("points", []):
            parts.extend((_text(point.get("title")), _text(point.get("description"))))
    elif kind == "comparison":
        for side in block.get("sides", []):
            parts.extend((_text(side.get("title")), _text(side.get("summary"))))
        for criterion in block.get("criteria", []):
            parts.extend(
                (
                    _text(criterion.get("label")),
                    _text(criterion.get("left")),
                    _text(criterion.get("right")),
                )
            )
    elif kind == "decision":
        parts.extend((_text(block.get("decision")), _text(block.get("rationale")), _text(block.get("owner"))))
        for option in block.get("options", []):
            parts.extend((_text(option.get("title")), _text(option.get("description"))))
    elif kind == "timeline":
        for step in block.get("steps", []):
            parts.extend((_text(step.get("label")), _text(step.get("title")), _text(step.get("owner"))))
    elif kind == "metric":
        parts.extend(
            (
                _text(block.get("value")),
                _text(block.get("label")),
                _text(block.get("context")),
                _text(block.get("source")),
            )
        )
    elif kind == "process":
        for step in block.get("steps", []):
            parts.extend((_text(step.get("title")), _text(step.get("description"))))
    elif kind == "quote":
        parts.extend(
            (_text(block.get("quote")), _text(block.get("attribution")), _text(block.get("evidence")))
        )
    elif kind == "table":
        parts.extend(_text(column) for column in block.get("columns", []))
        for row in block.get("rows", []):
            parts.extend(_text(cell) for cell in row.get("cells", []))
        parts.append(_text(block.get("accessible_summary")))
    elif kind == "chart":
        parts.extend(
            (
                _text(block.get("title")),
                _text(block.get("chart_type")),
                _text(block.get("category_field")),
                *(_text(value) for value in block.get("value_fields", [])),
                _text(block.get("source_note")),
            )
        )
    elif kind == "image":
        parts.extend(
            (
                _text(block.get("alt_text")),
                _text(block.get("caption")),
                _text(block.get("asset_id")),
            )
        )
    return " | ".join(part for part in parts if part)
