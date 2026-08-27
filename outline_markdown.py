"""Small deterministic Markdown interchange for reviewed Storyboard outlines."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

SLIDE_RE = re.compile(
    r"^##\s+(\d{1,2})\s+—\s+(.+?)"
    r"(?:\s+\[layout=(left|right|focus)\])?"
    r"(?:\s+\[block=(standard|comparison|decision|timeline|metric|process|quote|table|chart|image)\])?\s*$"
)
BULLET_RE = re.compile(r"^-\s+\*\*(.+?)\*\*\s+—\s+(.+?)\s*$")
META_RE = re.compile(r"^<!-- storyboard:meta (.+) -->$")
CONTENT_BLOCK_RE = re.compile(r"^<!-- storyboard:content-block (.+) -->$")
SOURCES_RE = re.compile(r"^<!-- storyboard:sources (.+) -->$")
NOTES_RE = re.compile(r"^<!-- storyboard:notes (.+) -->$")


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def presentation_to_markdown(
    data: Mapping[str, Any], *, story_metadata: Mapping[str, Any] | None = None
) -> str:
    lines = [f"# {data.get('title', 'Untitled presentation')}", f"> {data.get('subtitle', '')}", ""]
    metadata = {
        "theme": data.get("theme", "midnight"),
        "citations_appendix": bool(data.get("citations_appendix", False)),
        "assets": data.get("assets", []),
        "brand_kit": data.get("brand_kit"),
    }
    if story_metadata is not None:
        metadata["story"] = dict(story_metadata)
    lines.extend([f"<!-- storyboard:meta {_json(metadata)} -->", ""])
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
        if slide.get("content_block"):
            lines.append(f"<!-- storyboard:content-block {_json(slide['content_block'])} -->")
        lines.append(f"<!-- storyboard:sources {_json(slide.get('sources', []))} -->")
        lines.append(f"<!-- storyboard:notes {_json(slide.get('speaker_notes', ''))} -->")
        for point in slide.get("bullet_points", [])[:3]:
            lines.append(f"- **{point.get('title', '')}** — {point.get('description', '')}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def story_to_markdown(data: Mapping[str, Any]) -> str:
    """Serialize a complete story while keeping its presentation human-reviewable."""
    presentation = data.get("presentation")
    if not isinstance(presentation, Mapping):
        raise ValueError("A story Markdown export requires a presentation object")
    envelope = {key: value for key, value in data.items() if key != "presentation"}
    return presentation_to_markdown(presentation, story_metadata=envelope)


def _metadata_from_markdown(markdown: str) -> dict[str, Any]:
    for line_number, line in enumerate(markdown.splitlines(), start=1):
        match = META_RE.match(line)
        if not match:
            continue
        try:
            value = json.loads(match.group(1))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid storyboard metadata at line {line_number}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"Storyboard metadata at line {line_number} must be a JSON object")
        return value
    return {}


def markdown_to_story(markdown: str, theme: str = "midnight") -> tuple[dict[str, Any], bool]:
    """Parse story Markdown and report whether a legacy presentation was wrapped."""
    presentation = markdown_to_presentation(markdown, theme)
    story_metadata = _metadata_from_markdown(markdown).get("story")
    if story_metadata is None:
        return (
            {
                "schema_version": "2",
                "kind": "freeform-outline",
                "template": "freeform",
                "presentation": presentation,
                "decision_brief": None,
                "planner": "imported",
                "provider_warning": (
                    "Imported explicitly from presentation Markdown; decision fields were not inferred."
                ),
                "author_edits": [],
                "finding_dispositions": [],
            },
            True,
        )
    if not isinstance(story_metadata, dict):
        raise ValueError("Storyboard story metadata must be a JSON object")
    return {**story_metadata, "presentation": presentation}, False


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
    while cursor < len(lines) and not lines[cursor].strip():
        cursor += 1
    metadata: dict[str, Any] = {}
    if cursor < len(lines):
        metadata_match = META_RE.match(lines[cursor])
        if metadata_match:
            try:
                metadata = json.loads(metadata_match.group(1))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid storyboard metadata at line {cursor + 1}") from exc
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
        while (
            cursor < len(lines)
            and lines[cursor].strip()
            and not lines[cursor].startswith("- ")
            and not lines[cursor].startswith("<!-- storyboard:")
        ):
            if lines[cursor].startswith("#"):
                raise ValueError(f"Unsupported nested heading at line {cursor + 1}")
            content_lines.append(lines[cursor].strip())
            cursor += 1
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        content_block = None
        sources: list[dict[str, Any]] = []
        speaker_notes = ""
        while cursor < len(lines) and lines[cursor].startswith("<!-- storyboard:"):
            comment = lines[cursor]
            try:
                if match := CONTENT_BLOCK_RE.match(comment):
                    content_block = json.loads(match.group(1))
                elif match := SOURCES_RE.match(comment):
                    sources = json.loads(match.group(1))
                elif match := NOTES_RE.match(comment):
                    speaker_notes = json.loads(match.group(1))
                else:
                    raise ValueError(f"Unsupported Storyboard metadata at line {cursor + 1}")
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid Storyboard JSON metadata at line {cursor + 1}") from exc
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
        if content_block is None and len(bullets) != 3:
            raise ValueError(f"Slide {number} must contain exactly three bullets")
        slide = {
            "slide_number": int(number),
            "title": slide_title,
            "content": " ".join(content_lines),
            "layout": layout or "right",
            "block": block or "standard",
            "bullet_points": bullets,
            "sources": sources,
            "speaker_notes": speaker_notes,
        }
        if content_block is not None:
            slide["content_block"] = content_block
        slides.append(slide)
    if not 3 <= len(slides) <= 10:
        raise ValueError("Markdown outline must contain 3–10 content slides")
    return {
        "title": title,
        "subtitle": subtitle,
        "theme": metadata.get("theme", theme),
        "slides": slides,
        "assets": metadata.get("assets", []),
        "brand_kit": metadata.get("brand_kit"),
        "citations_appendix": bool(metadata.get("citations_appendix", False)),
    }
