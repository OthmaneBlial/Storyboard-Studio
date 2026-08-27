"""Portable Narrative Receipt creation, verification, and story diffs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from schemas import StoryDocumentV2
from storyboard_studio import __version__
from storyboard_studio.doctor import diagnose_story
from storyboard_studio.evidence import approved_citations, evidence_coverage
from storyboard_studio.semantic import block_plain_text, normalize_content_block


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def digest_value(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def create_receipt(
    story: StoryDocumentV2,
    story_path: Path,
    presentation_path: Path,
    *,
    viewer_status: str = "not-run",
) -> dict[str, Any]:
    report = diagnose_story(story)
    coverage = evidence_coverage(story.presentation)
    source_count = sum(len(slide.sources) for slide in story.presentation.slides)
    unresolved = [
        finding["code"]
        for finding in report["findings"]
        if finding.get("disposition") not in {"ignored", "resolved"}
    ]
    return {
        "schema_version": "1",
        "story_schema_version": story.schema_version,
        "template": story.template,
        "planner": story.planner,
        "provider_warning": story.provider_warning,
        "author_edits": story.author_edits,
        "outline_sha256": digest_value(story.presentation.model_dump(mode="json")),
        "story_sha256": digest_file(story_path),
        "doctor": {
            "status": report["status"],
            "summary": report["summary"],
            "findings": report["findings"],
            "dispositions": [item.model_dump(mode="json") for item in story.finding_dispositions],
        },
        "source_coverage": {
            "slides": len(story.presentation.slides),
            "sourced_slides": report["summary"]["sourced_slides"],
            "source_entries": source_count,
            "local_assets": len(story.presentation.assets),
            "claims": coverage["summary"]["claims"],
            "linked_claims": coverage["summary"]["linked_claims"],
            "author_checked_claims": coverage["summary"]["author_checked_claims"],
            "unresolved_claims": coverage["summary"]["unresolved_claims"],
        },
        "evidence_coverage": coverage,
        "source_provenance": [
            {"slide_number": slide.slide_number, **source.model_dump(mode="json")}
            for slide in story.presentation.slides
            for source in slide.sources
        ],
        "approved_citations": approved_citations(story.presentation),
        "citations_appendix": story.presentation.citations_appendix,
        "asset_provenance": [asset.model_dump(mode="json") for asset in story.presentation.assets],
        "unresolved_gaps": unresolved,
        "renderer_version": __version__,
        "viewer_status": viewer_status,
        "artifacts": {
            "story": {"path": story_path.name, "sha256": digest_file(story_path)},
            "presentation": {
                "path": presentation_path.name,
                "sha256": digest_file(presentation_path),
            },
        },
        "disclaimer": (
            "Hashes prove internal integrity only; they do not verify factual truth or source accuracy."
        ),
    }


def verify_receipt(receipt_path: Path) -> dict[str, Any]:
    with receipt_path.open(encoding="utf-8") as file:
        receipt = json.load(file)
    errors: list[str] = []
    for field in (
        "story_schema_version",
        "template",
        "outline_sha256",
        "doctor",
        "source_coverage",
        "renderer_version",
        "artifacts",
    ):
        if field not in receipt:
            errors.append(f"Required receipt field is missing: {field}.")
    if receipt.get("schema_version") != "1":
        errors.append("Unsupported receipt schema version.")
    artifacts = receipt.get("artifacts")
    if not isinstance(artifacts, dict):
        errors.append("Receipt artifacts are missing.")
        artifacts = {}
    checked: list[str] = []
    for name in ("story", "presentation"):
        entry = artifacts.get(name)
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            errors.append(f"Artifact reference is missing: {name}.")
            continue
        candidate = (receipt_path.parent / entry["path"]).resolve()
        try:
            candidate.relative_to(receipt_path.parent.resolve())
        except ValueError:
            errors.append(f"Artifact path escapes the receipt directory: {name}.")
            continue
        if not candidate.is_file():
            errors.append(f"Artifact is missing: {entry['path']}.")
            continue
        if digest_file(candidate) != entry.get("sha256"):
            errors.append(f"Artifact digest mismatch: {entry['path']}.")
            continue
        checked.append(name)
        if name == "story":
            try:
                with candidate.open(encoding="utf-8") as file:
                    story = StoryDocumentV2.model_validate(json.load(file))
                outline_digest = digest_value(story.presentation.model_dump(mode="json"))
                if outline_digest != receipt.get("outline_sha256"):
                    errors.append("The story outline digest does not match the receipt.")
                if story.schema_version != receipt.get("story_schema_version"):
                    errors.append("The story schema version does not match the receipt.")
            except (OSError, ValueError, json.JSONDecodeError):
                errors.append("The story artifact is not a valid schema v2 document.")
    return {
        "status": "verified" if not errors else "invalid",
        "checked": checked,
        "errors": errors,
        "disclaimer": (
            "Integrity verification does not establish the factual truth of presentation content."
        ),
    }


def diff_stories(old: StoryDocumentV2, new: StoryDocumentV2) -> dict[str, Any]:
    changes: list[dict[str, Any]] = []

    def compare(path: str, before: Any, after: Any) -> None:
        if before != after:
            changes.append({"path": path, "before": before, "after": after})

    compare("kind", old.kind, new.kind)
    compare("template", old.template, new.template)
    compare("presentation.title", old.presentation.title, new.presentation.title)
    compare("presentation.subtitle", old.presentation.subtitle, new.presentation.subtitle)
    compare("presentation.theme", old.presentation.theme, new.presentation.theme)
    compare(
        "presentation.citations_appendix",
        old.presentation.citations_appendix,
        new.presentation.citations_appendix,
    )
    compare(
        "presentation.sequence",
        [slide.title for slide in old.presentation.slides],
        [slide.title for slide in new.presentation.slides],
    )
    compare(
        "presentation.claims",
        [
            {
                "slide": slide.slide_number,
                "summary": slide.content,
                "semantic_block": block_plain_text(normalize_content_block(slide.model_dump(mode="json"))),
            }
            for slide in old.presentation.slides
        ],
        [
            {
                "slide": slide.slide_number,
                "summary": slide.content,
                "semantic_block": block_plain_text(normalize_content_block(slide.model_dump(mode="json"))),
            }
            for slide in new.presentation.slides
        ],
    )
    compare(
        "presentation.evidence",
        [source.model_dump(mode="json") for slide in old.presentation.slides for source in slide.sources],
        [source.model_dump(mode="json") for slide in new.presentation.slides for source in slide.sources],
    )
    compare(
        "presentation.evidence_owners",
        [source.owner for slide in old.presentation.slides for source in slide.sources],
        [source.owner for slide in new.presentation.slides for source in slide.sources],
    )
    compare(
        "presentation.assets",
        [asset.model_dump(mode="json") for asset in old.presentation.assets],
        [asset.model_dump(mode="json") for asset in new.presentation.assets],
    )
    if old.decision_brief and new.decision_brief:
        for field in ("decision", "audience", "desired_outcome", "owner", "next_step", "review_date"):
            compare(
                f"decision_brief.{field}",
                getattr(old.decision_brief, field),
                getattr(new.decision_brief, field),
            )
        compare(
            "decision_brief.options",
            [item.model_dump(mode="json") for item in old.decision_brief.options],
            [item.model_dump(mode="json") for item in new.decision_brief.options],
        )
        compare(
            "decision_brief.trade_offs",
            old.decision_brief.trade_offs,
            new.decision_brief.trade_offs,
        )
        compare(
            "decision_brief.evidence",
            [item.model_dump(mode="json") for item in old.decision_brief.evidence],
            [item.model_dump(mode="json") for item in new.decision_brief.evidence],
        )
    return {"schema_version": "1", "changed": bool(changes), "changes": changes}


def diff_to_markdown(report: dict[str, Any]) -> str:
    lines = ["# Storyboard story diff", ""]
    if not report["changes"]:
        return "\n".join([*lines, "No story changes.", ""])
    for change in report["changes"]:
        lines.extend(
            [
                f"## {change['path']}",
                "",
                f"- Before: `{canonical_json(change['before'])}`",
                f"- After: `{canonical_json(change['after'])}`",
                "",
            ]
        )
    return "\n".join(lines)
