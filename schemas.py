"""Strict public request and presentation contracts."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SlideConfig(StrictModel):
    focus: str = Field(default="", max_length=180)
    layout: Literal["left", "right", "focus"] = "right"
    block: Literal["standard", "comparison", "decision", "timeline", "metric"] = "standard"


class GenerateContentRequest(StrictModel):
    topic: str = Field(min_length=3, max_length=240)
    slide_count: int = Field(default=5, ge=3, le=10)
    brief: str = Field(default="", max_length=600)
    use_ai: bool = True
    slide_configs: list[SlideConfig] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def config_count_matches_slides(self) -> GenerateContentRequest:
        if self.slide_configs and len(self.slide_configs) != self.slide_count:
            raise ValueError("Provide one slide configuration per requested slide, or none.")
        return self


class BulletPoint(StrictModel):
    label: str = Field(min_length=1, max_length=8)
    title: str = Field(min_length=1, max_length=62)
    description: str = Field(min_length=1, max_length=120)


class SourceReference(StrictModel):
    label: str = Field(min_length=1, max_length=100)
    evidence: str = Field(default="", max_length=300)
    owner: str = Field(default="", max_length=80)


class DecisionOption(StrictModel):
    title: str = Field(min_length=1, max_length=70)
    description: str = Field(min_length=1, max_length=220)


class DecisionBriefV2(StrictModel):
    schema_version: Literal["2"] = "2"
    template: Literal["decision-brief"] = "decision-brief"
    decision: str = Field(min_length=3, max_length=240)
    audience: str = Field(min_length=3, max_length=180)
    desired_outcome: str = Field(min_length=3, max_length=240)
    current_context: str = Field(min_length=3, max_length=600)
    constraints: list[str] = Field(min_length=1, max_length=3)
    options: list[DecisionOption] = Field(min_length=2, max_length=3)
    trade_offs: list[str] = Field(min_length=1, max_length=3)
    evidence: list[SourceReference] = Field(default_factory=list, max_length=6)
    owner: str = Field(min_length=2, max_length=80)
    next_step: str = Field(min_length=3, max_length=240)
    review_date: date

    @field_validator("constraints", "trade_offs")
    @classmethod
    def non_empty_items(cls, values: list[str]) -> list[str]:
        if any(not value.strip() for value in values):
            raise ValueError("List items cannot be empty.")
        return values


class SlideContent(StrictModel):
    slide_number: int = Field(ge=1, le=10)
    title: str = Field(min_length=1, max_length=68)
    content: str = Field(min_length=1, max_length=220)
    bullet_points: list[BulletPoint] = Field(min_length=3, max_length=3)
    layout: Literal["left", "right", "focus"] = "right"
    block: Literal["standard", "comparison", "decision", "timeline", "metric"] = "standard"
    sources: list[SourceReference] = Field(default_factory=list, max_length=6)
    speaker_notes: str = Field(default="", max_length=1200)


class PresentationPayload(StrictModel):
    title: str = Field(min_length=1, max_length=90)
    subtitle: str = Field(default="", max_length=110)
    theme: Literal["midnight", "glacier", "ember", "forest", "royal", "sakura"] = "midnight"
    slides: list[SlideContent] = Field(min_length=3, max_length=10)

    @field_validator("slides")
    @classmethod
    def sequential_slide_numbers(cls, slides: list[SlideContent]) -> list[SlideContent]:
        expected = list(range(1, len(slides) + 1))
        actual = [slide.slide_number for slide in slides]
        if actual != expected:
            raise ValueError("Slide numbers must start at 1 and be sequential.")
        return slides


class FindingDisposition(StrictModel):
    code: str = Field(min_length=3, max_length=80)
    path: str = Field(default="presentation", max_length=180)
    status: Literal["accepted", "ignored", "resolved"]
    reason: str = Field(default="", max_length=300)


class StoryDocumentV2(StrictModel):
    schema_version: Literal["2"] = "2"
    kind: Literal["decision-brief", "freeform-outline"]
    template: Literal["decision-brief", "freeform"]
    presentation: PresentationPayload
    decision_brief: DecisionBriefV2 | None = None
    planner: Literal["local", "gemini", "imported", "authored"] = "local"
    provider_warning: str = Field(default="", max_length=300)
    author_edits: list[str] = Field(default_factory=list, max_length=100)
    finding_dispositions: list[FindingDisposition] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def decision_brief_matches_kind(self) -> StoryDocumentV2:
        if self.kind == "decision-brief" and self.decision_brief is None:
            raise ValueError("A decision-brief story requires decision_brief data.")
        if self.kind == "freeform-outline" and self.decision_brief is not None:
            raise ValueError("A freeform story cannot silently reinterpret a decision brief.")
        return self


class GuidedDecisionRequest(StrictModel):
    brief: DecisionBriefV2
    theme: Literal["midnight", "glacier", "ember", "forest", "royal", "sakura"] = "midnight"


class ExportPresentationRequest(StrictModel):
    presentation: PresentationPayload
