"""Content planning providers for Storyboard Studio.

The local planner is deliberately useful on its own. Gemini is an optional
enhancement, never a runtime requirement and never a source of stored secrets.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from storyboard_studio.providers import (
    EXCLUDED_FIELDS,
    TRANSFERRED_FIELDS,
    ProviderId,
    ProviderInput,
    catalog_entry,
    configured_provider,
    provider_timeout,
    selected_provider,
)

SUPPORTED_BLOCKS = {
    "standard",
    "comparison",
    "decision",
    "timeline",
    "metric",
    "process",
    "quote",
    "table",
}


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
        if config.get("block") in SUPPORTED_BLOCKS:
            slide["block"] = config["block"]
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
                "block": (block if block in SUPPORTED_BLOCKS else "standard"),
                "sources": sources,
                "speaker_notes": _clean(model_slide.get("speaker_notes"), 1200),
            }
        )
    return result


@dataclass(frozen=True)
class GenerationRun:
    presentation: dict[str, Any]
    source: str
    warning: str | None
    provider: dict[str, object]


def _run_metadata(
    selected: ProviderId,
    *,
    used: ProviderId,
    network_status: str,
    fallback_reason: dict[str, str] | None,
    environment: dict[str, str] | None,
) -> dict[str, object]:
    selected_entry = catalog_entry(selected, environment)
    used_entry = catalog_entry(used, environment)
    return {
        "selected": selected,
        "used": used,
        "label": selected_entry["label"],
        "model": selected_entry["model"],
        "used_model": used_entry["model"],
        "status": selected_entry["status"],
        "configured": selected_entry["configured"],
        "network_boundary": selected_entry["network_boundary"],
        "network_status": network_status,
        "structured_output": selected_entry["structured_output"],
        "timeout_seconds": selected_entry["timeout_seconds"],
        "cost_disclosure": selected_entry["cost_disclosure"],
        "retention_disclosure": selected_entry["retention_disclosure"],
        "transferred_fields": list(TRANSFERRED_FIELDS),
        "excluded_fields": list(EXCLUDED_FIELDS),
        "fallback_reason": fallback_reason,
    }


def generate_ppt_content_run(
    topic: str,
    slide_count: int,
    brief: str = "",
    slide_configs: list[dict[str, Any]] | None = None,
    use_ai: bool = True,
    provider: ProviderId | None = None,
    *,
    environment: dict[str, str] | None = None,
) -> GenerationRun:
    """Run one explicit adapter and return its full network/fallback provenance."""
    selected = selected_provider(provider, use_ai)
    local = build_local_presentation(topic, slide_count, brief, slide_configs)
    if selected == "local":
        return GenerationRun(
            local,
            "local",
            None,
            _run_metadata(
                selected,
                used="local",
                network_status="offline",
                fallback_reason=None,
                environment=environment,
            ),
        )

    try:
        adapter = configured_provider(selected, environment)
    except ValueError:
        adapter = None
    if adapter is None:
        message = (
            f"{catalog_entry(selected, environment)['label']} is not configured; "
            "the local planner ran instead."
        )
        fallback = {"code": f"{selected}-not-configured", "message": message}
        return GenerationRun(
            local,
            "local",
            message,
            _run_metadata(
                selected,
                used="local",
                network_status="not-sent",
                fallback_reason=fallback,
                environment=environment,
            ),
        )

    request = ProviderInput(
        topic=topic,
        slide_count=slide_count,
        brief=brief,
        slide_focuses=tuple(
            _clean(item.get("focus", ""), 120)
            for item in (slide_configs or [])
            if _clean(item.get("focus", ""), 120)
        ),
    )
    try:
        raw = adapter.generate(request, provider_timeout(environment))
        presentation = normalize_presentation(raw, topic, slide_count, brief, slide_configs)
        network_status = "external-completed" if selected == "gemini" else "loopback-completed"
        return GenerationRun(
            presentation,
            selected,
            None,
            _run_metadata(
                selected,
                used=selected,
                network_status=network_status,
                fallback_reason=None,
                environment=environment,
            ),
        )
    except Exception:
        # Provider errors are intentionally reduced to stable codes and never echo credentials or URLs.
        message = (
            f"{catalog_entry(selected, environment)['label']} was unavailable; the local planner ran instead."
        )
        fallback = {"code": f"{selected}-unavailable", "message": message}
        network_status = "external-attempted" if selected == "gemini" else "loopback-attempted"
        return GenerationRun(
            local,
            "local",
            message,
            _run_metadata(
                selected,
                used="local",
                network_status=network_status,
                fallback_reason=fallback,
                environment=environment,
            ),
        )


def generate_ppt_content(
    topic: str,
    slide_count: int,
    brief: str = "",
    slide_configs: list[dict[str, Any]] | None = None,
    use_ai: bool = True,
    provider: ProviderId | None = None,
) -> tuple[dict[str, Any], str, str | None]:
    """Compatibility wrapper for integrations that still consume the original tuple."""
    run = generate_ppt_content_run(topic, slide_count, brief, slide_configs, use_ai, provider)
    return run.presentation, run.source, run.warning
