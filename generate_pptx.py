"""A small, dependable PowerPoint renderer for Storyboard Studio.

The renderer has no network dependency. It accepts normalized presentation data
and produces an editable 16:9 PPTX using only native PowerPoint elements.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Mapping
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

THEMES: dict[str, dict[str, str]] = {
    "midnight": {
        "name": "Midnight editorial",
        "bg": "101425",
        "surface": "1B2136",
        "surface_alt": "262E49",
        "text": "F7F4EE",
        "muted": "B8C0D6",
        "accent": "E5B560",
        "accent_soft": "745B36",
    },
    "glacier": {
        "name": "Glacier field notes",
        "bg": "F4F8F8",
        "surface": "E4EFF0",
        "surface_alt": "D4E5E7",
        "text": "123544",
        "muted": "55727A",
        "accent": "0A7C86",
        "accent_soft": "B8D9D7",
    },
    "ember": {
        "name": "Ember study",
        "bg": "25120F",
        "surface": "38201A",
        "surface_alt": "4B2A21",
        "text": "FFF5E7",
        "muted": "D6B9A8",
        "accent": "F08A4B",
        "accent_soft": "79432B",
    },
    "forest": {
        "name": "Forest fieldwork",
        "bg": "F1F5EE",
        "surface": "E0EADD",
        "surface_alt": "D0DFC9",
        "text": "1D3829",
        "muted": "577060",
        "accent": "438360",
        "accent_soft": "B9D1BE",
    },
    "royal": {
        "name": "Royal archive",
        "bg": "17151B",
        "surface": "28242D",
        "surface_alt": "37313D",
        "text": "F5ECD8",
        "muted": "C7B99A",
        "accent": "C79C54",
        "accent_soft": "6E5735",
    },
    "sakura": {
        "name": "Sakura notebook",
        "bg": "FCF4F4",
        "surface": "F7E5E7",
        "surface_alt": "F0D5DA",
        "text": "4D2736",
        "muted": "846274",
        "accent": "BE526D",
        "accent_soft": "E5B8C4",
    },
}

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)
DISPLAY_FONT = "Aptos Display"
BODY_FONT = "Aptos"

try:
    PACKAGE_VERSION = version("storyboard-studio")
except PackageNotFoundError:  # pragma: no cover - source checkout without metadata
    PACKAGE_VERSION = "0.1.1"


def _rgb(value: str) -> RGBColor:
    return RGBColor.from_string(value.replace("#", "").upper())


def _as_text(value: Any, limit: int, fallback: str = "") -> str:
    if not isinstance(value, str):
        return fallback
    value = " ".join(value.split())
    return value[:limit] if value else fallback


def _set_fill(shape: Any, color: RGBColor) -> None:
    shape.fill.solid()
    shape.fill.fore_color.rgb = color
    shape.line.fill.background()


def _add_text(
    slide: Any,
    text: str,
    x: Any,
    y: Any,
    w: Any,
    h: Any,
    *,
    size: float,
    color: RGBColor,
    font: str = BODY_FONT,
    bold: bool = False,
    align: Any = PP_ALIGN.LEFT,
    valign: Any = MSO_ANCHOR.TOP,
    margins: float = 0.0,
) -> Any:
    box = slide.shapes.add_textbox(x, y, w, h)
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(margins)
    frame.margin_right = Inches(margins)
    frame.margin_top = Inches(margins)
    frame.margin_bottom = Inches(margins)
    frame.vertical_anchor = valign
    paragraph = frame.paragraphs[0]
    paragraph.alignment = align
    run = paragraph.add_run()
    run.text = text
    run.font.name = font
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    return box


def _base_slide(prs: Presentation, theme: Mapping[str, str]) -> Any:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = _rgb(theme["bg"])
    return slide


def _add_footer(slide: Any, data: Mapping[str, Any], theme: Mapping[str, str], page: int) -> None:
    _add_text(
        slide,
        _as_text(data.get("title"), 58),
        Inches(0.55),
        Inches(7.05),
        Inches(6.2),
        Inches(0.22),
        size=9,
        color=_rgb(theme["muted"]),
    )
    _add_text(
        slide,
        str(page).zfill(2),
        Inches(12.1),
        Inches(7.03),
        Inches(0.65),
        Inches(0.22),
        size=9,
        color=_rgb(theme["muted"]),
        align=PP_ALIGN.RIGHT,
    )


def _add_notes(slide: Any, slide_data: Mapping[str, Any]) -> None:
    """Write optional author notes and source references to native PPTX notes."""
    notes = _as_text(slide_data.get("speaker_notes"), 1200)
    sources = slide_data.get("sources")
    rows = []
    if isinstance(sources, list):
        for source in sources[:6]:
            if isinstance(source, Mapping):
                label = _as_text(source.get("label"), 100)
                evidence = _as_text(source.get("evidence"), 300)
                owner = _as_text(source.get("owner"), 80)
                if label:
                    rows.append(" — ".join(part for part in (label, evidence, owner) if part))
    if rows:
        source_text = "Sources / evidence (author-supplied; not verified):\n" + "\n".join(rows)
        notes = f"{notes}\n\n{source_text}" if notes else source_text
    if notes:
        slide.notes_slide.notes_text_frame.text = notes


def _add_title_slide(prs: Presentation, data: Mapping[str, Any], theme: Mapping[str, str]) -> None:
    slide = _base_slide(prs, theme)
    bg = _rgb(theme["bg"])
    surface = _rgb(theme["surface"])
    accent = _rgb(theme["accent"])
    text = _rgb(theme["text"])
    muted = _rgb(theme["muted"])

    left_rule = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0.55), Inches(0.65), Inches(0.1), Inches(5.9)
    )
    _set_fill(left_rule, accent)
    panel = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(9.75), Inches(0), Inches(3.583), Inches(7.5))
    _set_fill(panel, surface)
    lower_panel = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(9.75), Inches(4.7), Inches(3.583), Inches(2.8)
    )
    _set_fill(lower_panel, accent)
    small_block = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(10.35), Inches(1.0), Inches(2.4), Inches(0.16)
    )
    _set_fill(small_block, accent)

    _add_text(
        slide,
        "STORYBOARD STUDIO",
        Inches(1.0),
        Inches(0.84),
        Inches(5.7),
        Inches(0.32),
        size=12,
        color=accent,
        bold=True,
    )
    _add_text(
        slide,
        _as_text(data.get("title"), 90, "Untitled presentation"),
        Inches(0.95),
        Inches(1.48),
        Inches(8.1),
        Inches(2.45),
        size=48,
        color=text,
        font=DISPLAY_FONT,
        bold=True,
    )
    _add_text(
        slide,
        _as_text(data.get("subtitle"), 110),
        Inches(1.0),
        Inches(4.28),
        Inches(7.55),
        Inches(0.85),
        size=21,
        color=muted,
    )
    _add_text(
        slide,
        "A concise, editable deck",
        Inches(10.35),
        Inches(1.42),
        Inches(2.25),
        Inches(0.6),
        size=17,
        color=text,
        bold=True,
    )
    _add_text(
        slide,
        "Prepared for a clear conversation, not a wall of slides.",
        Inches(10.35),
        Inches(2.25),
        Inches(2.25),
        Inches(1.05),
        size=16,
        color=muted,
    )
    _add_text(
        slide,
        "EDITABLE\nPOWERPOINT",
        Inches(10.35),
        Inches(5.25),
        Inches(2.2),
        Inches(1.2),
        size=20,
        color=bg,
        font=DISPLAY_FONT,
        bold=True,
    )


def _add_content_slide(
    prs: Presentation,
    data: Mapping[str, Any],
    slide_data: Mapping[str, Any],
    theme: Mapping[str, str],
    page: int,
) -> None:
    slide = _base_slide(prs, theme)
    text = _rgb(theme["text"])
    muted = _rgb(theme["muted"])
    accent = _rgb(theme["accent"])
    surface = _rgb(theme["surface"])
    surface_alt = _rgb(theme["surface_alt"])
    layout = slide_data.get("layout") if slide_data.get("layout") in {"left", "right", "focus"} else "right"
    block = (
        slide_data.get("block")
        if slide_data.get("block") in {"standard", "comparison", "decision", "timeline", "metric"}
        else "standard"
    )

    if layout == "focus":
        visual_x, visual_w = Inches(9.45), Inches(3.15)
        content_x, content_w = Inches(0.6), Inches(8.25)
    elif layout == "left":
        visual_x, visual_w = Inches(0.6), Inches(3.5)
        content_x, content_w = Inches(4.55), Inches(7.8)
    else:
        visual_x, visual_w = Inches(9.15), Inches(3.65)
        content_x, content_w = Inches(0.6), Inches(7.8)

    accent_bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.13), SLIDE_HEIGHT)
    _set_fill(accent_bar, accent)
    block_labels = {
        "standard": "KEY FRAME",
        "comparison": "COMPARE",
        "decision": "DECISION",
        "timeline": "SEQUENCE",
        "metric": "SIGNAL",
    }
    _add_text(
        slide,
        "STORYBOARD / " + str(page).zfill(2),
        Inches(0.58),
        Inches(0.42),
        Inches(2.2),
        Inches(0.28),
        size=10,
        color=accent,
        bold=True,
    )
    heading_x = content_x if layout == "left" else Inches(0.55)
    heading_width = content_w if layout == "left" else Inches(7.7 if layout != "focus" else 11.6)
    intro_x = content_x if layout == "left" else Inches(0.6)
    intro_width = content_w if layout == "left" else Inches(7.0 if layout != "focus" else 8.35)

    _add_text(
        slide,
        _as_text(slide_data.get("title"), 68, f"Slide {page}"),
        heading_x,
        Inches(0.88),
        heading_width,
        Inches(0.75),
        size=35,
        color=text,
        font=DISPLAY_FONT,
        bold=True,
    )
    _add_text(
        slide,
        _as_text(slide_data.get("content"), 220),
        intro_x,
        Inches(1.82),
        intro_width,
        Inches(1.12),
        size=18,
        color=muted,
    )

    visual = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, visual_x, Inches(1.78), visual_w, Inches(4.58)
    )
    _set_fill(visual, surface)
    visual_inner = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, visual_x + Inches(0.32), Inches(2.12), visual_w - Inches(0.64), Inches(0.12)
    )
    _set_fill(visual_inner, accent)
    _add_text(
        slide,
        str(page).zfill(2),
        visual_x + Inches(0.32),
        Inches(2.5),
        visual_w - Inches(0.64),
        Inches(1.25),
        size=58,
        color=accent,
        font=DISPLAY_FONT,
        bold=True,
    )
    _add_text(
        slide,
        block_labels[block],
        visual_x + Inches(0.34),
        Inches(3.87),
        visual_w - Inches(0.68),
        Inches(0.25),
        size=11,
        color=muted,
        bold=True,
    )
    if block == "comparison":
        split_width = (visual_w - Inches(0.78)) / 2
        before = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, visual_x + Inches(0.34), Inches(5.15), split_width, Inches(0.55)
        )
        _set_fill(before, accent)
        _add_text(
            slide,
            "BEFORE",
            before.left,
            before.top + Inches(0.12),
            before.width,
            Inches(0.25),
            size=9,
            color=text,
            bold=True,
            align=PP_ALIGN.CENTER,
        )
        after = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE,
            visual_x + Inches(0.44) + split_width,
            Inches(5.15),
            split_width,
            Inches(0.55),
        )
        _set_fill(after, surface_alt)
        _add_text(
            slide,
            "AFTER",
            after.left,
            after.top + Inches(0.12),
            after.width,
            Inches(0.25),
            size=9,
            color=text,
            bold=True,
            align=PP_ALIGN.CENTER,
        )
    elif block == "timeline":
        for marker in range(3):
            dot = slide.shapes.add_shape(
                MSO_SHAPE.OVAL,
                visual_x + Inches(0.5) + Inches(marker * 0.82),
                Inches(5.15),
                Inches(0.28),
                Inches(0.28),
            )
            _set_fill(dot, accent if marker == 0 else surface_alt)
    elif block == "metric":
        _add_text(
            slide,
            "03",
            visual_x + Inches(0.34),
            Inches(5.0),
            visual_w - Inches(0.68),
            Inches(0.72),
            size=32,
            color=accent,
            font=DISPLAY_FONT,
            bold=True,
        )
    elif block == "decision":
        decision = slide.shapes.add_shape(
            MSO_SHAPE.CHEVRON, visual_x + Inches(0.36), Inches(5.14), visual_w - Inches(0.72), Inches(0.52)
        )
        _set_fill(decision, accent)
    _add_text(
        slide,
        _as_text(slide_data.get("title"), 48),
        visual_x + Inches(0.34),
        Inches(4.28),
        visual_w - Inches(0.68),
        Inches(1.12),
        size=19,
        color=text,
        font=DISPLAY_FONT,
        bold=True,
    )

    raw_bullets = slide_data.get("bullet_points")
    bullet_points = raw_bullets if isinstance(raw_bullets, list) else []
    for index in range(3):
        candidate = bullet_points[index] if index < len(bullet_points) else {}
        bullet = candidate if isinstance(candidate, Mapping) else {}
        y = Inches(3.25 + index * 1.08)
        row = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, content_x, y, content_w, Inches(0.82))
        _set_fill(row, surface if index % 2 == 0 else surface_alt)
        label = _as_text(bullet.get("label"), 8, str(index + 1).zfill(2))
        _add_text(
            slide,
            label,
            content_x + Inches(0.2),
            y + Inches(0.21),
            Inches(0.54),
            Inches(0.3),
            size=12,
            color=accent,
            bold=True,
        )
        _add_text(
            slide,
            _as_text(bullet.get("title"), 62, f"Point {index + 1}"),
            content_x + Inches(0.78),
            y + Inches(0.15),
            Inches(2.45),
            Inches(0.31),
            size=16,
            color=text,
            bold=True,
        )
        _add_text(
            slide,
            _as_text(bullet.get("description"), 120),
            content_x + Inches(3.28),
            y + Inches(0.15),
            content_w - Inches(3.48),
            Inches(0.38),
            size=15,
            color=muted,
        )
    _add_footer(slide, data, theme, page)
    _add_notes(slide, slide_data)


def create_presentation(
    data: Mapping[str, Any], output_path: str | Path = "output/storyboard-presentation.pptx"
) -> Path:
    """Render a validated payload to a new file and return its absolute path."""
    theme_id = data.get("theme", "midnight") if isinstance(data, Mapping) else "midnight"
    theme = THEMES.get(str(theme_id), THEMES["midnight"])
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT
    prs.core_properties.title = _as_text(data.get("title"), 90, "Storyboard Studio presentation")
    prs.core_properties.subject = _as_text(data.get("subtitle"), 110)
    prs.core_properties.author = "Storyboard Studio"

    _add_title_slide(prs, data, theme)
    slides = data.get("slides") if isinstance(data.get("slides"), list) else []
    for page, slide_data in enumerate(slides, start=1):
        if isinstance(slide_data, Mapping):
            _add_content_slide(prs, data, slide_data, theme, page)

    destination = Path(output_path).expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    prs.save(destination)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render Storyboard Studio JSON into an editable PowerPoint deck."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {PACKAGE_VERSION}")
    parser.add_argument("--input", required=True, type=Path, help="Validated presentation JSON file")
    parser.add_argument(
        "--output", type=Path, default=Path("output/storyboard.pptx"), help="Destination PPTX path"
    )
    args = parser.parse_args()
    try:
        with args.input.open(encoding="utf-8") as file:
            from schemas import PresentationPayload

            data = PresentationPayload.model_validate(json.load(file)).model_dump()
        output = create_presentation(data, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(f"Could not create the presentation: {exc}")
    print(f"Created {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
