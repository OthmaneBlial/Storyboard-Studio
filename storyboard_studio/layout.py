"""Validated layout, theme, brand-kit, and overflow contracts.

The browser and PowerPoint renderer both consume the same runtime token file.
No font, image, or theme resource is fetched from the network.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

THEME_IDS = ("midnight", "glacier", "ember", "forest", "royal", "sakura")
GENERIC_FONT_FAMILIES = {"serif", "sans-serif", "monospace", "system-ui"}


class LayoutContractError(ValueError):
    """Raised when a runtime layout or brand contract is unsafe or incomplete."""


class LayoutModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _relative_luminance(value: str) -> float:
    channels = [int(value[index : index + 2], 16) / 255 for index in (0, 2, 4)]
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast_ratio(first: str, second: str) -> float:
    lighter, darker = sorted((_relative_luminance(first), _relative_luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


class ThemeColors(LayoutModel):
    bg: str
    surface: str
    surface_alt: str
    text: str
    muted: str
    accent: str
    accent_soft: str

    @field_validator("bg", "surface", "surface_alt", "text", "muted", "accent", "accent_soft")
    @classmethod
    def valid_hex_color(cls, value: str) -> str:
        normalized = value.removeprefix("#").upper()
        if len(normalized) != 6 or any(character not in "0123456789ABCDEF" for character in normalized):
            raise ValueError("Colors must be six-digit hexadecimal RGB values.")
        return normalized

    @model_validator(mode="after")
    def accessible_contrast(self) -> ThemeColors:
        checks = {
            "text/background": (self.text, self.bg, 4.5),
            "muted/background": (self.muted, self.bg, 4.5),
            "text/surface": (self.text, self.surface, 4.5),
            "accent/background": (self.accent, self.bg, 3.0),
        }
        failures = [
            f"{label} {contrast_ratio(first, second):.2f}:1 (needs {minimum:.1f}:1)"
            for label, (first, second, minimum) in checks.items()
            if contrast_ratio(first, second) < minimum
        ]
        if failures:
            raise ValueError("Insufficient color contrast: " + "; ".join(failures))
        return self


class ThemeTokens(ThemeColors):
    label: str = Field(min_length=1, max_length=48)


class CanvasTokens(LayoutModel):
    width_inches: float = Field(gt=10, le=20)
    height_inches: float = Field(gt=5, le=12)
    aspect_ratio: str = Field(pattern=r"^16:9$")

    @model_validator(mode="after")
    def true_widescreen_ratio(self) -> CanvasTokens:
        if abs(self.width_inches / self.height_inches - 16 / 9) > 0.002:
            raise ValueError("Canvas dimensions must resolve to a 16:9 aspect ratio.")
        return self


class TypographyTokens(LayoutModel):
    title_pt: float = Field(ge=24, le=54)
    summary_pt: float = Field(ge=12, le=28)
    body_pt: float = Field(ge=8, le=20)
    label_pt: float = Field(ge=7, le=14)
    footer_pt: float = Field(ge=7, le=12)


class FrameTokens(LayoutModel):
    x: float = Field(ge=0)
    y: float = Field(ge=0)
    width: float = Field(gt=0)
    height: float = Field(gt=0)


class LayoutVariant(LayoutModel):
    heading: FrameTokens
    summary: FrameTokens
    content: FrameTokens
    visual: FrameTokens


class OverflowVariant(LayoutModel):
    title_characters: int = Field(ge=32, le=90)
    summary_characters: int = Field(ge=90, le=260)
    block_characters: int = Field(ge=180, le=1600)


class OverflowTokens(LayoutModel):
    layouts: dict[Literal["left", "right", "focus"], OverflowVariant]


class LayoutContract(LayoutModel):
    schema_version: Literal["2"]
    canvas: CanvasTokens
    safe_area_inches: float = Field(ge=0.35, le=1.0)
    font_fallbacks: dict[Literal["display", "body"], list[str]]
    typography: TypographyTokens
    layouts: dict[Literal["left", "right", "focus"], LayoutVariant]
    overflow: OverflowTokens
    themes: dict[str, ThemeTokens]

    @field_validator("font_fallbacks")
    @classmethod
    def safe_font_stacks(cls, stacks: dict[str, list[str]]) -> dict[str, list[str]]:
        for role, fonts in stacks.items():
            if len(fonts) < 2 or len(fonts) > 6:
                raise ValueError(f"The {role} font stack must contain 2–6 local fallbacks.")
            if fonts[-1].lower() not in GENERIC_FONT_FAMILIES:
                raise ValueError(f"The {role} font stack must end with a generic family.")
            if any("://" in font or len(font) > 80 for font in fonts):
                raise ValueError("Font fallbacks must be local family names, never URLs.")
        return stacks

    @model_validator(mode="after")
    def complete_and_bounded(self) -> LayoutContract:
        if set(self.themes) != set(THEME_IDS):
            raise ValueError("Runtime tokens must define exactly the six public theme ids.")
        width, height = self.canvas.width_inches, self.canvas.height_inches
        for layout_name, layout in self.layouts.items():
            for frame_name, frame in (
                ("heading", layout.heading),
                ("summary", layout.summary),
                ("content", layout.content),
                ("visual", layout.visual),
            ):
                if frame.x + frame.width > width or frame.y + frame.height > height:
                    raise ValueError(f"{layout_name}.{frame_name} leaves the 16:9 canvas.")
        return self


class BrandKit(LayoutModel):
    schema_version: Literal["1"] = "1"
    name: str = Field(min_length=1, max_length=60)
    base_theme: Literal["midnight", "glacier", "ember", "forest", "royal", "sakura"]
    colors: ThemeColors
    display_font_fallbacks: list[str] = Field(min_length=2, max_length=6)
    body_font_fallbacks: list[str] = Field(min_length=2, max_length=6)

    @field_validator("display_font_fallbacks", "body_font_fallbacks")
    @classmethod
    def safe_brand_fonts(cls, fonts: list[str]) -> list[str]:
        if fonts[-1].lower() not in GENERIC_FONT_FAMILIES:
            raise ValueError("A brand font stack must end with a generic family.")
        if any("://" in font or len(font) > 80 for font in fonts):
            raise ValueError("Brand fonts must be local family names, never URLs.")
        return fonts


def default_layout_path() -> Path:
    configured = os.getenv("STORYBOARD_THEME_TOKENS", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    checkout = Path(__file__).resolve().parents[1] / "themes" / "storyboard-tokens.json"
    if checkout.is_file():
        return checkout
    return Path(__file__).resolve().parent / "data" / "storyboard-tokens.json"


def load_layout_contract(path: str | Path | None = None) -> LayoutContract:
    source = Path(path).expanduser().resolve() if path else default_layout_path()
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
        return LayoutContract.model_validate(raw)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise LayoutContractError(f"Invalid local layout contract {source}: {exc}") from exc


def load_brand_kit(path: str | Path) -> BrandKit:
    source = Path(path).expanduser().resolve()
    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
        return BrandKit.model_validate(raw)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise LayoutContractError(f"Invalid local brand kit {source}: {exc}") from exc


def active_theme(
    contract: LayoutContract,
    theme_id: str,
    brand_kit: BrandKit | Mapping[str, Any] | None = None,
) -> tuple[dict[str, str], list[str], list[str]]:
    selected = contract.themes.get(theme_id, contract.themes["midnight"])
    colors = selected.model_dump(exclude={"label"})
    display_fonts = contract.font_fallbacks["display"]
    body_fonts = contract.font_fallbacks["body"]
    if brand_kit:
        kit = brand_kit if isinstance(brand_kit, BrandKit) else BrandKit.model_validate(brand_kit)
        colors = kit.colors.model_dump()
        display_fonts = kit.display_font_fallbacks
        body_fonts = kit.body_font_fallbacks
    return colors, display_fonts, body_fonts


def _semantic_text(block: object) -> str:
    if not isinstance(block, Mapping):
        return ""
    parts: list[str] = []
    for key, value in block.items():
        if key in {"type", "asset_id", "fit"}:
            continue
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            for item in value:
                parts.append(_semantic_text(item) if isinstance(item, Mapping) else str(item))
        elif isinstance(value, Mapping):
            parts.append(_semantic_text(value))
    return " ".join(parts)


def analyze_overflow(presentation: Mapping[str, Any], contract: LayoutContract) -> dict[str, Any]:
    """Return deterministic pre-export findings from the shared layout budget."""
    findings: list[dict[str, Any]] = []
    slides = presentation.get("slides") if isinstance(presentation.get("slides"), list) else []
    for index, slide in enumerate(slides):
        if not isinstance(slide, Mapping):
            continue
        layout_name = str(slide.get("layout", "right"))
        if layout_name not in contract.overflow.layouts:
            layout_name = "right"
        limits = contract.overflow.layouts[layout_name]
        values = (
            ("title", str(slide.get("title", "")), limits.title_characters),
            ("content", str(slide.get("content", "")), limits.summary_characters),
            ("content_block", _semantic_text(slide.get("content_block")), limits.block_characters),
        )
        for field, value, limit in values:
            if len(value) <= limit:
                continue
            actions = (
                [{"id": "review-block", "label": "Review block copy"}]
                if field == "content_block"
                else [{"id": "shorten", "label": f"Shorten to {limit} characters"}]
            )
            if layout_name != "focus":
                actions.append({"id": "use-focus", "label": "Use focus layout"})
            content_block = slide.get("content_block")
            if (
                field == "content"
                and isinstance(content_block, Mapping)
                and content_block.get("type") == "standard"
                and len(content_block.get("points", [])) > 1
            ):
                actions.append({"id": "split", "label": "Split into two slides"})
            findings.append(
                {
                    "code": f"overflow.{field}",
                    "slide_index": index,
                    "slide_number": index + 1,
                    "path": f"slides.{index}.{field}",
                    "field": field,
                    "characters": len(value),
                    "limit": limit,
                    "message": (
                        f"Slide {index + 1} {field.replace('_', ' ')} uses {len(value)} characters "
                        f"inside a {limit}-character {layout_name} layout budget."
                    ),
                    "actions": actions,
                }
            )
    return {
        "schema_version": "1",
        "status": "needs-fix" if findings else "ready",
        "findings": findings,
        "layout_schema": contract.schema_version,
    }
