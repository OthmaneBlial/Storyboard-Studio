"""Versioned story documents and deterministic decision-brief planning."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from schemas import (
    BulletPoint,
    DecisionBriefV2,
    PresentationPayload,
    SlideContent,
    SourceReference,
    StoryDocumentV2,
)


def _clip(value: str, limit: int) -> str:
    return " ".join(value.split())[:limit]


def _points(values: list[tuple[str, str]]) -> list[BulletPoint]:
    return [
        BulletPoint(label=str(index).zfill(2), title=_clip(title, 62), description=_clip(body, 120))
        for index, (title, body) in enumerate(values[:3], start=1)
    ]


def _fill_three(
    values: list[str],
    fallbacks: list[tuple[str, str]],
    *,
    title: str,
) -> list[tuple[str, str]]:
    rows = [(f"{title} {index}", value) for index, value in enumerate(values, start=1)]
    rows.extend(fallbacks[: 3 - len(rows)])
    return rows[:3]


def build_decision_story(brief: DecisionBriefV2, theme: str = "midnight") -> StoryDocumentV2:
    """Compile only author-provided decision fields into a stable five-slide story."""
    sources = [SourceReference.model_validate(item) for item in brief.evidence]
    constraint_rows = _fill_three(
        brief.constraints,
        [
            ("Decision boundary", brief.decision),
            ("Intended outcome", brief.desired_outcome),
        ],
        title="Constraint",
    )
    option_rows = [(option.title, option.description) for option in brief.options]
    if len(option_rows) < 3:
        option_rows.append(("Decision lens", brief.constraints[0]))
    tradeoff_rows = _fill_three(
        brief.trade_offs,
        [
            ("What the decision protects", brief.desired_outcome),
            ("Who must be served", brief.audience),
        ],
        title="Trade-off",
    )
    slides = [
        SlideContent(
            slide_number=1,
            title="The decision in context",
            content=_clip(brief.current_context, 220),
            bullet_points=_points(
                [
                    ("Audience", brief.audience),
                    ("Desired outcome", brief.desired_outcome),
                    ("Decision", brief.decision),
                ]
            ),
            layout="right",
            block="standard",
            sources=sources,
        ),
        SlideContent(
            slide_number=2,
            title="The boundaries that matter",
            content="The decision must work inside these author-defined constraints.",
            bullet_points=_points(constraint_rows),
            layout="left",
            block="comparison",
        ),
        SlideContent(
            slide_number=3,
            title="The options on the table",
            content="Compare only the options and decision lens supplied in the brief.",
            bullet_points=_points(option_rows),
            layout="focus",
            block="comparison",
        ),
        SlideContent(
            slide_number=4,
            title="The trade-off to accept",
            content=_clip(brief.decision, 220),
            bullet_points=_points(tradeoff_rows),
            layout="right",
            block="decision",
            sources=sources,
        ),
        SlideContent(
            slide_number=5,
            title="The owned next step",
            content=_clip(brief.next_step, 220),
            bullet_points=_points(
                [
                    ("Owner", brief.owner),
                    ("Next step", brief.next_step),
                    ("Review date", brief.review_date.isoformat()),
                ]
            ),
            layout="left",
            block="timeline",
        ),
    ]
    presentation = PresentationPayload(
        title=_clip(brief.decision, 90),
        subtitle=_clip(f"For {brief.audience} — {brief.desired_outcome}", 110),
        theme=theme,
        slides=slides,
    )
    return StoryDocumentV2(
        kind="decision-brief",
        template="decision-brief",
        presentation=presentation,
        decision_brief=brief,
        planner="local",
    )


def migrate_presentation_v1(presentation: PresentationPayload) -> StoryDocumentV2:
    """Wrap a validated v1 outline without inventing structured decision fields."""
    return StoryDocumentV2(
        kind="freeform-outline",
        template="freeform",
        presentation=presentation,
        planner="imported",
        provider_warning=(
            "Migrated explicitly from a v1 freeform outline; decision-brief fields were not inferred."
        ),
    )


def parse_story_or_presentation(value: Any) -> tuple[StoryDocumentV2, bool]:
    """Return a story and whether the source required an explicit v1 wrapper."""
    if isinstance(value, dict) and value.get("schema_version") == "2":
        return StoryDocumentV2.model_validate(value), False
    return migrate_presentation_v1(PresentationPayload.model_validate(value)), True


def read_story_or_presentation(path: Path) -> tuple[StoryDocumentV2, bool]:
    try:
        with path.open(encoding="utf-8") as file:
            return parse_story_or_presentation(json.load(file))
    except ValidationError:
        raise
