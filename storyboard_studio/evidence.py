"""Deterministic claim extraction, evidence coverage, and citations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from schemas import PresentationPayload
from storyboard_studio.semantic import normalize_content_block


def _text(value: object) -> str:
    return " ".join(str(value or "").split())


def _block_claims(block: Mapping[str, Any] | None) -> list[str]:
    if not block:
        return []
    block_type = block.get("type", "standard")
    rows: list[str] = []
    if block_type == "standard":
        rows = [
            f"{_text(item.get('title'))}: {_text(item.get('description'))}"
            for item in block.get("points", [])
        ]
    elif block_type == "comparison":
        rows = [
            f"{_text(item.get('title'))}: {_text(item.get('summary'))}" for item in block.get("sides", [])
        ]
        rows.extend(
            f"{_text(item.get('label'))}: {_text(item.get('left'))} / {_text(item.get('right'))}"
            for item in block.get("criteria", [])
        )
    elif block_type == "decision":
        rows = [_text(block.get("decision"))]
        rows.extend(
            f"{_text(item.get('title'))}: {_text(item.get('description'))}"
            for item in block.get("options", [])
        )
        rows.append(_text(block.get("rationale")))
    elif block_type == "timeline":
        rows = [
            f"{_text(item.get('label'))}: {_text(item.get('title'))} — {_text(item.get('owner'))}"
            for item in block.get("steps", [])
        ]
    elif block_type == "metric":
        rows = [f"{_text(block.get('value'))} {_text(block.get('label'))}: {_text(block.get('context'))}"]
    elif block_type == "process":
        rows = [
            f"{_text(item.get('title'))}: {_text(item.get('description'))}" for item in block.get("steps", [])
        ]
    elif block_type == "quote":
        rows = [f"{_text(block.get('quote'))} — {_text(block.get('attribution'))}"]
    elif block_type == "table":
        rows = [_text(block.get("accessible_summary"))]
    elif block_type == "chart":
        rows = [f"{_text(block.get('title'))}: {_text(block.get('source_note'))}"]
    elif block_type == "image":
        rows = [_text(block.get("caption")) or _text(block.get("alt_text"))]
    return [row for row in rows if row.strip(" :—/")]


def extract_claims(value: PresentationPayload | Mapping[str, Any]) -> list[dict[str, Any]]:
    payload = value if isinstance(value, PresentationPayload) else PresentationPayload.model_validate(value)
    claims: list[dict[str, Any]] = []
    for slide in payload.slides:
        claims.append(
            {
                "id": "summary",
                "slide_number": slide.slide_number,
                "path": f"slides[{slide.slide_number - 1}].content",
                "text": slide.content,
                "kind": "summary",
            }
        )
        block = normalize_content_block(slide.model_dump(mode="json"))
        for index, text in enumerate(_block_claims(block), start=1):
            claims.append(
                {
                    "id": f"block-{index}",
                    "slide_number": slide.slide_number,
                    "path": f"slides[{slide.slide_number - 1}].content_block",
                    "text": text,
                    "kind": "semantic-block",
                }
            )
    return claims


def evidence_coverage(value: PresentationPayload | Mapping[str, Any]) -> dict[str, Any]:
    payload = value if isinstance(value, PresentationPayload) else PresentationPayload.model_validate(value)
    claims = extract_claims(payload)
    sources_by_slide = {slide.slide_number: slide.sources for slide in payload.slides}
    claim_rows: list[dict[str, Any]] = []
    for claim in claims:
        linked = [
            source for source in sources_by_slide[claim["slide_number"]] if claim["id"] in source.claim_ids
        ]
        checked = [source for source in linked if source.review_status == "author-checked"]
        status = "author-checked" if checked else ("linked-unresolved" if linked else "unresolved")
        claim_rows.append(
            {
                **claim,
                "status": status,
                "source_labels": [source.label for source in linked],
                "has_url": any(bool(source.url) for source in linked),
                "disclaimer": "A locator or URL does not verify this claim.",
            }
        )
    slides = []
    for slide in payload.slides:
        slide_claims = [claim for claim in claim_rows if claim["slide_number"] == slide.slide_number]
        slides.append(
            {
                "slide_number": slide.slide_number,
                "title": slide.title,
                "claims": len(slide_claims),
                "linked_claims": sum(claim["status"] != "unresolved" for claim in slide_claims),
                "author_checked_claims": sum(claim["status"] == "author-checked" for claim in slide_claims),
                "unresolved_claims": sum(claim["status"] != "author-checked" for claim in slide_claims),
                "source_entries": len(slide.sources),
            }
        )
    checked_claims = sum(claim["status"] == "author-checked" for claim in claim_rows)
    linked_claims = sum(claim["status"] != "unresolved" for claim in claim_rows)
    return {
        "schema_version": "1",
        "summary": {
            "slides": len(payload.slides),
            "claims": len(claim_rows),
            "linked_claims": linked_claims,
            "author_checked_claims": checked_claims,
            "unresolved_claims": len(claim_rows) - checked_claims,
            "source_entries": sum(len(slide.sources) for slide in payload.slides),
        },
        "slides": slides,
        "claims": claim_rows,
        "disclaimer": ("Coverage records author links and checks; it does not establish factual truth."),
    }


def approved_citations(value: PresentationPayload | Mapping[str, Any]) -> list[dict[str, Any]]:
    payload = value if isinstance(value, PresentationPayload) else PresentationPayload.model_validate(value)
    merged: dict[tuple[str, ...], dict[str, Any]] = {}
    for slide in payload.slides:
        for source in slide.sources:
            if source.review_status != "author-checked":
                continue
            raw = source.model_dump(mode="json")
            key = tuple(
                str(raw.get(field) or "")
                for field in (
                    "label",
                    "evidence",
                    "owner",
                    "url",
                    "local_reference",
                    "checked_date",
                    "license",
                )
            )
            entry = merged.setdefault(
                key,
                {
                    **raw,
                    "slides": [],
                    "claim_ids_by_slide": {},
                },
            )
            entry["slides"].append(slide.slide_number)
            entry["claim_ids_by_slide"][str(slide.slide_number)] = list(source.claim_ids)
    return list(merged.values())
