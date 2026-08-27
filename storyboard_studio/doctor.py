"""Deterministic narrative diagnostics shared by CLI, API, and browser clients."""

from __future__ import annotations

import re
from itertools import combinations
from typing import Any

from schemas import PresentationPayload

WORD_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)
NUMBER_RE = re.compile(r"(?<![\w/])(?:[$€£]\s*)?\d+(?:[.,]\d+)?%?(?![\w/])")
DECISION_WORDS = {"decide", "choose", "recommend", "approve", "select", "selected"}
TRADE_OFF_WORDS = {"trade-off", "tradeoff", "versus", "vs", "instead", "constraint", "option"}
ACTION_WORDS = {"action", "next", "owner", "milestone", "approve", "start", "ship", "decide"}


def _words(value: str) -> set[str]:
    return {word.lower() for word in WORD_RE.findall(value) if len(word) > 2}


def _slide_text(slide: dict[str, Any]) -> str:
    parts = [str(slide.get("title", "")), str(slide.get("content", ""))]
    for point in slide.get("bullet_points", []):
        parts.extend((str(point.get("title", "")), str(point.get("description", ""))))
    return " ".join(parts)


def _finding(
    code: str,
    severity: str,
    message: str,
    action: str,
    *,
    path: str = "presentation",
    slide_number: int | None = None,
) -> dict[str, Any]:
    finding: dict[str, Any] = {
        "code": code,
        "severity": severity,
        "path": path,
        "message": message,
        "action": action,
    }
    if slide_number is not None:
        finding["slide_number"] = slide_number
    return finding


def diagnose_presentation(value: dict[str, Any] | PresentationPayload) -> dict[str, Any]:
    """Return stable, explainable findings without making factual claims."""
    payload = value if isinstance(value, PresentationPayload) else PresentationPayload.model_validate(value)
    data = payload.model_dump()
    slides = data["slides"]
    findings: list[dict[str, Any]] = []

    subtitle_words = _words(data["subtitle"])
    if len(subtitle_words) < 4 or data["subtitle"].lower() == "a concise, editable briefing":
        findings.append(
            _finding(
                "audience.unclear",
                "warning",
                "The subtitle does not identify a clear audience or desired outcome.",
                "Name who must understand or decide what after reading this deck.",
                path="subtitle",
            )
        )

    all_text = " ".join(_slide_text(slide) for slide in slides).lower()
    all_words = _words(all_text)
    if not (DECISION_WORDS & all_words):
        findings.append(
            _finding(
                "decision.missing",
                "error",
                "The story does not make the decision or recommendation explicit.",
                "Add one sentence that states what the audience is being asked to choose or approve.",
            )
        )
    if not any(word in all_text for word in TRADE_OFF_WORDS):
        findings.append(
            _finding(
                "tradeoff.missing",
                "warning",
                "No trade-off, constraint, or alternative is visible in the story.",
                "Show the meaningful alternative and why the proposed direction is preferable.",
            )
        )

    for slide in slides:
        number = slide["slide_number"]
        text = _slide_text(slide)
        sources = slide.get("sources", [])
        if NUMBER_RE.search(text) and not sources:
            findings.append(
                _finding(
                    "evidence.numeric-claim",
                    "warning",
                    "This slide contains a numeric claim but no author-supplied source.",
                    "Add the source and evidence owner, or rewrite the number as an explicit assumption.",
                    path=f"slides[{number - 1}].sources",
                    slide_number=number,
                )
            )
        for source_index, source in enumerate(sources):
            if not source.get("owner"):
                findings.append(
                    _finding(
                        "evidence.owner-missing",
                        "info",
                        "An evidence entry has no accountable owner.",
                        "Name who can confirm or refresh this evidence.",
                        path=f"slides[{number - 1}].sources[{source_index}].owner",
                        slide_number=number,
                    )
                )
        copy_size = len(slide["content"]) + sum(
            len(point["title"]) + len(point["description"]) for point in slide["bullet_points"]
        )
        if copy_size > 430:
            findings.append(
                _finding(
                    "copy.dense",
                    "warning",
                    "This slide is likely too dense for the supported layout.",
                    "Shorten the summary, split the slide, or move detail into speaker notes.",
                    path=f"slides[{number - 1}]",
                    slide_number=number,
                )
            )

    for left, right in combinations(slides, 2):
        left_words = _words(_slide_text(left))
        right_words = _words(_slide_text(right))
        union = left_words | right_words
        similarity = len(left_words & right_words) / len(union) if union else 0
        if similarity >= 0.72:
            findings.append(
                _finding(
                    "story.duplicate",
                    "warning",
                    (
                        f"Slides {left['slide_number']} and {right['slide_number']} "
                        "make substantially similar points."
                    ),
                    "Merge them or give each slide a distinct narrative role.",
                    path="slides",
                )
            )

    last_slide = slides[-1]
    last_words = _words(_slide_text(last_slide))
    if not (ACTION_WORDS & last_words):
        findings.append(
            _finding(
                "action.missing",
                "error",
                "The final slide does not contain a clear next action, owner, or milestone.",
                "End with one accountable owner, one next action, and one review point.",
                path=f"slides[{len(slides) - 1}]",
                slide_number=last_slide["slide_number"],
            )
        )

    sourced = sum(1 for slide in slides if slide.get("sources"))
    severity_counts = {
        severity: sum(1 for finding in findings if finding["severity"] == severity)
        for severity in ("error", "warning", "info")
    }
    return {
        "schema_version": "1",
        "status": "ready" if not severity_counts["error"] else "needs-review",
        "summary": {
            "slides": len(slides),
            "sourced_slides": sourced,
            "errors": severity_counts["error"],
            "warnings": severity_counts["warning"],
            "information": severity_counts["info"],
        },
        "findings": findings,
        "disclaimer": (
            "This structural and provenance report does not verify factual truth or source accuracy."
        ),
    }


def diagnosis_to_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Storyboard Doctor report",
        "",
        f"Status: **{report['status']}**",
        "",
        (
            f"Slides: {summary['slides']} · sourced: {summary['sourced_slides']} · "
            f"errors: {summary['errors']} · warnings: {summary['warnings']} · "
            f"information: {summary['information']}"
        ),
        "",
    ]
    if report["findings"]:
        for finding in report["findings"]:
            location = f" — slide {finding['slide_number']}" if "slide_number" in finding else ""
            lines.extend(
                [
                    f"## {finding['severity'].upper()}: {finding['code']}{location}",
                    "",
                    finding["message"],
                    "",
                    f"**Action:** {finding['action']}",
                    "",
                ]
            )
    else:
        lines.extend(["No structural findings.", ""])
    lines.extend([f"> {report['disclaimer']}", ""])
    return "\n".join(lines)
