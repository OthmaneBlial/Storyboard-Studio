"""Small deterministic Markdown interchange for reviewed Storyboard outlines."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

SLIDE_RE = re.compile(
    r"^##\s+(\d{1,2})\s+—\s+(.+?)"
    r"(?:\s+\[layout=(left|right|focus)\])?"
    r"(?:\s+\[block=(standard|comparison|decision|timeline|metric)\])?\s*$"
)
BULLET_RE = re.compile(r"^-\s+\*\*(.+?)\*\*\s+—\s+(.+?)\s*$")


def presentation_to_markdown(data: Mapping[str, Any]) -> str:
    lines = [f"# {data.get('title', 'Untitled presentation')}", f"> {data.get('subtitle', '')}", ""]
    for slide in data.get("slides", []):
        number = int(slide.get("slide_number", len(lines)))
        layout = slide.get("layout", "right")
        block = slide.get("block", "standard")
        lines.extend(
            [
                f"## {number:02d} — {slide.get('title', 'Untitled slide')} [layout={layout}] [block={block}]",
                "",
                str(slide.get("content", "")),
                "",
            ]
        )
        for point in slide.get("bullet_points", [])[:3]:
            lines.append(f"- **{point.get('title', '')}** — {point.get('description', '')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def markdown_to_presentation(markdown: str, theme: str = "midnight") -> dict[str, Any]:
    lines = markdown.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError("Markdown outline must start with a single '# Title' heading")
    title = lines[0][2:].strip()
    subtitle = ""
    cursor = 1
    while cursor < len(lines) and not lines[cursor].strip():
        cursor += 1
    if cursor < len(lines) and lines[cursor].startswith("> "):
        subtitle = lines[cursor][2:].strip()
        cursor += 1
    slides = []
    while cursor < len(lines):
        if not lines[cursor].strip():
            cursor += 1
            continue
        match = SLIDE_RE.match(lines[cursor])
        if not match:
            raise ValueError(f"Unsupported Markdown construct at line {cursor + 1}; expected a slide heading")
        number, slide_title, layout, block = match.groups()
        cursor += 1
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        content_lines = []
        while cursor < len(lines) and lines[cursor].strip() and not lines[cursor].startswith("- "):
            if lines[cursor].startswith("#"):
                raise ValueError(f"Unsupported nested heading at line {cursor + 1}")
            content_lines.append(lines[cursor].strip())
            cursor += 1
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        bullets = []
        while cursor < len(lines) and lines[cursor].startswith("- "):
            bullet = BULLET_RE.match(lines[cursor])
            if not bullet:
                raise ValueError(f"Unsupported bullet syntax at line {cursor + 1}")
            bullet_title, description = bullet.groups()
            bullets.append(
                {"label": f"{len(bullets) + 1:02d}", "title": bullet_title, "description": description}
            )
            cursor += 1
        if len(bullets) != 3:
            raise ValueError(f"Slide {number} must contain exactly three bullets")
        slides.append(
            {
                "slide_number": int(number),
                "title": slide_title,
                "content": " ".join(content_lines),
                "layout": layout or "right",
                "block": block or "standard",
                "bullet_points": bullets,
            }
        )
    if not 3 <= len(slides) <= 10:
        raise ValueError("Markdown outline must contain 3–10 content slides")
    return {"title": title, "subtitle": subtitle, "theme": theme, "slides": slides}
