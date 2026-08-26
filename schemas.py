"""Strict public request and presentation contracts."""

from __future__ import annotations

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


class SlideContent(StrictModel):
    slide_number: int = Field(ge=1, le=10)
    title: str = Field(min_length=1, max_length=68)
    content: str = Field(min_length=1, max_length=220)
    bullet_points: list[BulletPoint] = Field(min_length=3, max_length=3)
    layout: Literal["left", "right", "focus"] = "right"
    block: Literal["standard", "comparison", "decision", "timeline", "metric"] = "standard"


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


class ExportPresentationRequest(StrictModel):
    presentation: PresentationPayload
