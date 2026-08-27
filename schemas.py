"""Strict public request and presentation contracts."""

from __future__ import annotations

from datetime import date
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from storyboard_studio.layout import BrandKit


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SlideConfig(StrictModel):
    focus: str = Field(default="", max_length=180)
    layout: Literal["left", "right", "focus"] = "right"
    block: Literal[
        "standard",
        "comparison",
        "decision",
        "timeline",
        "metric",
        "process",
        "quote",
        "table",
    ] = "standard"


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


class StandardBlock(StrictModel):
    type: Literal["standard"] = "standard"
    points: list[BulletPoint] = Field(min_length=1, max_length=4)


class ComparisonSide(StrictModel):
    title: str = Field(min_length=1, max_length=70)
    summary: str = Field(min_length=1, max_length=180)


class ComparisonCriterion(StrictModel):
    label: str = Field(min_length=1, max_length=60)
    left: str = Field(min_length=1, max_length=120)
    right: str = Field(min_length=1, max_length=120)


class ComparisonBlock(StrictModel):
    type: Literal["comparison"] = "comparison"
    sides: list[ComparisonSide] = Field(min_length=2, max_length=2)
    criteria: list[ComparisonCriterion] = Field(min_length=1, max_length=3)


class DecisionBlock(StrictModel):
    type: Literal["decision"] = "decision"
    decision: str = Field(min_length=1, max_length=180)
    options: list[DecisionOption] = Field(min_length=2, max_length=3)
    rationale: str = Field(min_length=1, max_length=220)
    owner: str = Field(default="", max_length=80)


class TimelineStep(StrictModel):
    label: str = Field(min_length=1, max_length=24)
    title: str = Field(min_length=1, max_length=80)
    owner: str = Field(default="", max_length=80)


class TimelineBlock(StrictModel):
    type: Literal["timeline"] = "timeline"
    steps: list[TimelineStep] = Field(min_length=2, max_length=4)


class MetricBlock(StrictModel):
    type: Literal["metric"] = "metric"
    value: str = Field(min_length=1, max_length=24)
    label: str = Field(min_length=1, max_length=80)
    context: str = Field(min_length=1, max_length=220)
    source: str = Field(default="", max_length=120)


class ProcessStep(StrictModel):
    title: str = Field(min_length=1, max_length=70)
    description: str = Field(min_length=1, max_length=140)


class ProcessBlock(StrictModel):
    type: Literal["process"] = "process"
    steps: list[ProcessStep] = Field(min_length=3, max_length=5)


class QuoteBlock(StrictModel):
    type: Literal["quote"] = "quote"
    quote: str = Field(min_length=1, max_length=280)
    attribution: str = Field(min_length=1, max_length=100)
    evidence: str = Field(default="", max_length=180)


class TableRow(StrictModel):
    cells: list[str] = Field(min_length=2, max_length=4)

    @field_validator("cells")
    @classmethod
    def non_empty_cells(cls, values: list[str]) -> list[str]:
        if any(not value.strip() or len(value) > 100 for value in values):
            raise ValueError("Table cells must contain 1–100 characters.")
        return values


class TableBlock(StrictModel):
    type: Literal["table"] = "table"
    columns: list[str] = Field(min_length=2, max_length=4)
    rows: list[TableRow] = Field(min_length=1, max_length=5)
    accessible_summary: str = Field(min_length=1, max_length=300)

    @field_validator("columns")
    @classmethod
    def non_empty_columns(cls, values: list[str]) -> list[str]:
        if any(not value.strip() or len(value) > 60 for value in values):
            raise ValueError("Table columns must contain 1–60 characters.")
        return values

    @model_validator(mode="after")
    def row_width_matches_columns(self) -> TableBlock:
        if any(len(row.cells) != len(self.columns) for row in self.rows):
            raise ValueError("Every table row must match the declared column count.")
        return self


class ChartBlock(StrictModel):
    type: Literal["chart"] = "chart"
    chart_type: Literal["bar", "line", "donut"]
    asset_id: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9._-]*$")
    category_field: str = Field(min_length=1, max_length=60)
    value_fields: list[str] = Field(min_length=1, max_length=3)
    title: str = Field(min_length=1, max_length=100)
    source_note: str = Field(min_length=1, max_length=180)

    @field_validator("value_fields")
    @classmethod
    def unique_value_fields(cls, values: list[str]) -> list[str]:
        if any(not value.strip() or len(value) > 60 for value in values):
            raise ValueError("Chart value fields must contain 1–60 characters.")
        if len(set(values)) != len(values):
            raise ValueError("Chart value fields must be unique.")
        return values


class ImageBlock(StrictModel):
    type: Literal["image"] = "image"
    asset_id: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9._-]*$")
    alt_text: str = Field(min_length=1, max_length=240)
    caption: str = Field(default="", max_length=160)
    fit: Literal["contain", "cover"] = "contain"


SemanticBlock = Annotated[
    StandardBlock
    | ComparisonBlock
    | DecisionBlock
    | TimelineBlock
    | MetricBlock
    | ProcessBlock
    | QuoteBlock
    | TableBlock
    | ChartBlock
    | ImageBlock,
    Field(discriminator="type"),
]


class LocalAsset(StrictModel):
    id: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9._-]*$")
    kind: Literal["data", "image"]
    path: str = Field(min_length=1, max_length=240)
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    media_type: Literal[
        "text/csv",
        "application/json",
        "image/png",
        "image/jpeg",
        "image/svg+xml",
    ]
    license: str = Field(min_length=1, max_length=100)
    attribution: str = Field(min_length=1, max_length=180)
    alt_text: str = Field(default="", max_length=240)
    source_note: str = Field(default="", max_length=180)

    @field_validator("path")
    @classmethod
    def local_relative_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if "://" in value or "\\" in value or path.is_absolute() or ".." in path.parts:
            raise ValueError("Asset paths must be local, POSIX-style, and relative.")
        return value

    @model_validator(mode="after")
    def kind_matches_media_type(self) -> LocalAsset:
        if self.kind == "data" and self.media_type not in {"text/csv", "application/json"}:
            raise ValueError("Data assets must use CSV or JSON media types.")
        if self.kind == "image" and not self.media_type.startswith("image/"):
            raise ValueError("Image assets must use PNG, JPEG, or SVG media types.")
        if self.kind == "data" and not self.source_note:
            raise ValueError("Data assets require a source note.")
        if self.kind == "image" and not self.alt_text:
            raise ValueError("Image assets require alt text.")
        return self


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
    bullet_points: list[BulletPoint] = Field(default_factory=list, max_length=3)
    layout: Literal["left", "right", "focus"] = "right"
    block: Literal[
        "standard",
        "comparison",
        "decision",
        "timeline",
        "metric",
        "process",
        "quote",
        "table",
        "chart",
        "image",
    ] = "standard"
    content_block: SemanticBlock | None = None
    sources: list[SourceReference] = Field(default_factory=list, max_length=6)
    speaker_notes: str = Field(default="", max_length=1200)

    @model_validator(mode="after")
    def semantic_or_v1_bullets(self) -> SlideContent:
        if self.content_block is None and len(self.bullet_points) != 3:
            raise ValueError("Legacy slides require exactly 3 bullet points.")
        if self.content_block is not None and self.content_block.type != self.block:
            raise ValueError("Slide block must match content_block.type.")
        return self


class PresentationPayload(StrictModel):
    title: str = Field(min_length=1, max_length=90)
    subtitle: str = Field(default="", max_length=110)
    theme: Literal["midnight", "glacier", "ember", "forest", "royal", "sakura"] = "midnight"
    slides: list[SlideContent] = Field(min_length=3, max_length=10)
    assets: list[LocalAsset] = Field(default_factory=list, max_length=12)
    brand_kit: BrandKit | None = None

    @field_validator("slides")
    @classmethod
    def sequential_slide_numbers(cls, slides: list[SlideContent]) -> list[SlideContent]:
        expected = list(range(1, len(slides) + 1))
        actual = [slide.slide_number for slide in slides]
        if actual != expected:
            raise ValueError("Slide numbers must start at 1 and be sequential.")
        return slides

    @field_validator("assets")
    @classmethod
    def unique_asset_ids(cls, assets: list[LocalAsset]) -> list[LocalAsset]:
        identifiers = [asset.id for asset in assets]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Asset ids must be unique.")
        return assets

    @model_validator(mode="after")
    def referenced_assets_exist(self) -> PresentationPayload:
        assets = {asset.id: asset for asset in self.assets}
        for slide in self.slides:
            if isinstance(slide.content_block, ChartBlock | ImageBlock):
                asset = assets.get(slide.content_block.asset_id)
                if asset is None:
                    raise ValueError(
                        f"Slide {slide.slide_number} references unknown asset "
                        f"{slide.content_block.asset_id!r}."
                    )
                expected_kind = "data" if isinstance(slide.content_block, ChartBlock) else "image"
                if asset.kind != expected_kind:
                    raise ValueError(f"Slide {slide.slide_number} requires a {expected_kind} asset.")
        return self


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
