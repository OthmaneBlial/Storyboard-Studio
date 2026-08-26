"""Content planning providers for Storyboard Studio.

The local planner is deliberately useful on its own. Gemini is an optional
enhancement, never a runtime requirement and never a source of stored secrets.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


def _clean(value: Any, limit: int, fallback: str = "") -> str:
    """Return predictable, presentation-safe text from an untrusted response."""
    if not isinstance(value, str):
        return fallback
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit] if value else fallback


def _title_from_topic(topic: str) -> str:
    words = _clean(topic, 90).split()
    return " ".join(words[:9]).title() or "Untitled presentation"


def _local_slide(topic: str, index: int, focus: str = "") -> dict[str, Any]:
    """Create a concise, editable slide without presenting made-up facts."""
    patterns = [
        (
            "The opportunity",
            "Frame the useful outcome before deciding how to deliver it.",
            [
                ("Audience first", "Name who benefits and what changes for them."),
                ("Concrete outcome", "Describe the result people should be able to see."),
                ("Useful boundary", "Keep the first version focused and testable."),
            ],
        ),
        (
            "What matters now",
            "Separate the signals worth acting on from noise and assumptions.",
            [
                ("Current context", "Capture the conditions shaping the decision today."),
                ("Key constraint", "Make the non-negotiable trade-off explicit."),
                ("Decision lens", "Use a shared criterion to prioritize the next move."),
            ],
        ),
        (
            "A practical approach",
            "Turn the idea into a small sequence that can be owned and improved.",
            [
                ("Start small", "Choose one meaningful workflow to prove the value."),
                ("Make it visible", "Give the team a simple way to inspect progress."),
                ("Learn quickly", "Use feedback to refine the next iteration."),
            ],
        ),
        (
            "The critical choices",
            "Good execution comes from choosing what to protect, measure, and defer.",
            [
                ("Protect trust", "Set clear expectations around quality and ownership."),
                ("Design for use", "Remove steps that do not help the intended audience."),
                ("Keep it adaptable", "Leave room for evidence to change the plan."),
            ],
        ),
        (
            "From intent to action",
            "Make the next milestone specific enough that progress is unmistakable.",
            [
                ("One accountable owner", "Assign responsibility for the immediate decision."),
                ("A visible milestone", "Define what completion looks like in plain language."),
                ("A review rhythm", "Decide when the result will be assessed together."),
            ],
        ),
        (
            "How to know it works",
            "Use a small set of measures that connect effort to the intended outcome.",
            [
                ("Adoption signal", "Observe whether the intended audience returns to it."),
                ("Quality signal", "Check whether the result meets the promised standard."),
                ("Learning signal", "Record what should change in the next cycle."),
            ],
        ),
    ]
    title, content, bullets = patterns[(index - 1) % len(patterns)]
    if focus:
        title = _clean(focus, 68, title)
        content = f"Use this slide to make the {title.lower()} decision clear for {topic}."

    blocks = ["comparison", "timeline", "decision", "metric", "standard", "standard"]
    return {
        "slide_number": index,
        "title": title,
        "content": _clean(content, 220),
        "bullet_points": [
            {"label": str(position + 1).zfill(2), "title": bullet[0], "description": bullet[1]}
            for position, bullet in enumerate(bullets)
        ],
        "layout": "focus" if index % 3 == 0 else "right",
        "block": blocks[(index - 1) % len(blocks)],
        "sources": [],
        "speaker_notes": "",
    }


def build_local_presentation(
    topic: str, slide_count: int, brief: str = "", slide_configs: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    """Build an honest starter narrative that users can edit before export."""
    configs = slide_configs or []
    slides = []
    for index in range(1, slide_count + 1):
        config = configs[index - 1] if index <= len(configs) else {}
        focus = _clean(config.get("focus", ""), 120)
        slide = _local_slide(topic, index, focus)
        if config.get("layout") in {"left", "right", "focus"}:
            slide["layout"] = config["layout"]
        slides.append(slide)

    subtitle = _clean(brief, 110, "A concise, editable briefing")
    return {
        "title": _title_from_topic(topic),
        "subtitle": subtitle,
        "theme": "midnight",
        "slides": slides,
    }


def normalize_presentation(
    raw: Any,
    topic: str,
    slide_count: int,
    brief: str = "",
    slide_configs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Limit and repair model output so the renderer only receives safe content."""
    fallback = build_local_presentation(topic, slide_count, brief, slide_configs)
    if not isinstance(raw, dict) or not isinstance(raw.get("slides"), list):
        return fallback

    result = {
        "title": _clean(raw.get("title"), 90, fallback["title"]),
        "subtitle": _clean(raw.get("subtitle"), 110, fallback["subtitle"]),
        "theme": "midnight",
        "slides": [],
    }
    configs = slide_configs or []
    for index in range(slide_count):
        model_slide = raw["slides"][index] if index < len(raw["slides"]) else {}
        default_slide = fallback["slides"][index]
        if not isinstance(model_slide, dict):
            model_slide = {}
        config = configs[index] if index < len(configs) else {}
        bullets: list[dict[str, str]] = []
        model_bullets = model_slide.get("bullet_points")
        if isinstance(model_bullets, list):
            for bullet_index, point in enumerate(model_bullets[:3]):
                default_point = default_slide["bullet_points"][bullet_index]
                if isinstance(point, dict):
                    title = _clean(point.get("title"), 62, default_point["title"])
                    description = _clean(point.get("description"), 120, default_point["description"])
                elif isinstance(point, list) and len(point) >= 3:
                    title = _clean(point[1], 62, default_point["title"])
                    description = _clean(point[2], 120, default_point["description"])
                else:
                    continue
                bullets.append(
                    {
                        "label": str(bullet_index + 1).zfill(2),
                        "title": title,
                        "description": description,
                    }
                )
        while len(bullets) < 3:
            bullets.append(default_slide["bullet_points"][len(bullets)])

        layout = config.get("layout", model_slide.get("layout", default_slide["layout"]))
        block = config.get("block", model_slide.get("block", default_slide.get("block", "standard")))
        raw_sources = model_slide.get("sources")
        sources = []
        if isinstance(raw_sources, list):
            for source in raw_sources[:6]:
                if (
                    isinstance(source, dict)
                    and isinstance(source.get("label"), str)
                    and source["label"].strip()
                ):
                    sources.append(
                        {
                            "label": _clean(source["label"], 100),
                            "evidence": _clean(source.get("evidence"), 300),
                            "owner": _clean(source.get("owner"), 80),
                        }
                    )
        result["slides"].append(
            {
                "slide_number": index + 1,
                "title": _clean(model_slide.get("title"), 68, default_slide["title"]),
                "content": _clean(model_slide.get("content"), 220, default_slide["content"]),
                "bullet_points": bullets,
                "layout": layout if layout in {"left", "right", "focus"} else default_slide["layout"],
                "block": (
                    block
                    if block in {"standard", "comparison", "decision", "timeline", "metric"}
                    else "standard"
                ),
                "sources": sources,
                "speaker_notes": _clean(model_slide.get("speaker_notes"), 1200),
            }
        )
    return result


def _gemini_content(
    topic: str, slide_count: int, brief: str, slide_configs: list[dict[str, Any]] | None
) -> dict[str, Any]:
    """Request structured content from Gemini. Imports are lazy for local-only use."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    try:
        from google import genai
    except ImportError as exc:  # pragma: no cover - exercised by installation checks
        raise RuntimeError("The optional Gemini dependency is not installed") from exc

    focus_notes = [item.get("focus", "") for item in (slide_configs or []) if item.get("focus")]
    prompt = f"""Create an editable {slide_count}-slide presentation outline.
Topic: {topic}
Audience / purpose: {brief or "General audience; make the core idea clear."}
Requested slide focuses: {json.dumps(focus_notes)}

Return JSON only with title, subtitle, and slides. Each slide needs title (max 8 words),
content (max 30 words), and exactly 3 bullet_points. A bullet point may be an object with
title and description, or a three-item array [label, title, description]. Do not invent
statistics, citations, or claims that cannot be supported. Keep wording concise and useful."""
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL),
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    return json.loads(response.text)


def generate_ppt_content(
    topic: str,
    slide_count: int,
    brief: str = "",
    slide_configs: list[dict[str, Any]] | None = None,
    use_ai: bool = True,
) -> tuple[dict[str, Any], str, str | None]:
    """Generate a normalized presentation and explain which provider was used."""
    if not use_ai or not os.getenv("GEMINI_API_KEY"):
        return build_local_presentation(topic, slide_count, brief, slide_configs), "local", None
    try:
        raw = _gemini_content(topic, slide_count, brief, slide_configs)
        return normalize_presentation(raw, topic, slide_count, brief, slide_configs), "gemini", None
    except Exception:
        # Do not echo provider exceptions: they can reveal deployment details or credentials.
        return (
            build_local_presentation(topic, slide_count, brief, slide_configs),
            "local",
            "Gemini was unavailable, so Storyboard created a local editable outline instead.",
        )
