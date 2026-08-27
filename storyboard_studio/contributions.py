"""Offline validation for public template and fixture contributions."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from generate_pptx import create_presentation
from storyboard_studio.doctor import diagnose_story
from storyboard_studio.layout import analyze_overflow, load_layout_contract
from storyboard_studio.receipt import digest_file
from storyboard_studio.story import read_story_or_presentation

ALLOWED_LICENSES = {"Apache-2.0", "CC-BY-4.0", "CC0-1.0", "MIT"}
SECRET_PREFIX_RE = re.compile(
    r"(?:sk-[A-Za-z0-9_-]{16,}|AIza[A-Za-z0-9_-]{20,}|gh[opsu]_[A-Za-z0-9]{20,}|"
    r"glpat-[A-Za-z0-9_-]{16,}|xox[baprs]-[A-Za-z0-9-]{16,})"
)
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
PERSONAL_PATH_RE = re.compile(r"(?:/Users/[^/\s]+/|/home/[^/\s]+/|[A-Za-z]:\\Users\\[^\\\s]+\\)")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@([A-Z0-9.-]+\.[A-Z]{2,})\b", re.IGNORECASE)
SENSITIVE_KEYS = {
    "api-key",
    "apikey",
    "api_key",
    "authorization",
    "password",
    "secret",
    "token",
}
SAFE_PLACEHOLDERS = {"", "example", "not-configured", "placeholder", "redacted", "synthetic"}


class ContributionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ContributionManifest(ContributionModel):
    schema_version: Literal["1"] = "1"
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{2,63}$")
    kind: Literal["template", "fixture"]
    content_path: str = Field(min_length=1, max_length=180)
    content_origin: Literal["synthetic", "public"]
    license: str = Field(min_length=2, max_length=40)
    attribution: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=10, max_length=300)

    @field_validator("content_path")
    @classmethod
    def safe_relative_content_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if "\\" in value or "://" in value or path.is_absolute() or ".." in path.parts:
            raise ValueError("Contribution content_path must be a relative POSIX path.")
        return value

    @field_validator("license")
    @classmethod
    def supported_public_license(cls, value: str) -> str:
        if value not in ALLOWED_LICENSES:
            raise ValueError(f"Contribution license must be one of: {', '.join(sorted(ALLOWED_LICENSES))}.")
        return value

    @model_validator(mode="after")
    def synthetic_templates_use_cc0(self) -> ContributionManifest:
        if self.kind == "template" and self.content_origin == "synthetic" and self.license != "CC0-1.0":
            raise ValueError("Synthetic public templates must use CC0-1.0.")
        return self


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key {key!r} is not allowed.")
        result[key] = value
    return result


def _walk_sensitive_values(value: Any, path: str = "content") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).lower().replace(" ", "_")
            if normalized in SENSITIVE_KEYS and str(item).strip().lower() not in SAFE_PLACEHOLDERS:
                findings.append(f"{path}.{key} contains a non-placeholder secret-like value")
            findings.extend(_walk_sensitive_values(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            findings.extend(_walk_sensitive_values(item, f"{path}[{index}]"))
    return findings


def privacy_findings(raw_text: str) -> list[str]:
    """Return high-confidence public-contribution privacy findings."""
    findings = []
    if SECRET_PREFIX_RE.search(raw_text):
        findings.append("content contains a credential-like token prefix")
    if PRIVATE_KEY_RE.search(raw_text):
        findings.append("content contains a private-key block")
    if PERSONAL_PATH_RE.search(raw_text):
        findings.append("content contains a personal absolute filesystem path")
    for domain in EMAIL_RE.findall(raw_text):
        if domain.lower() not in {"example.com", "example.net", "example.org"}:
            findings.append("content contains a non-example email address")
            break
    try:
        value = json.loads(raw_text)
    except json.JSONDecodeError:
        value = None
    if value is not None:
        findings.extend(_walk_sensitive_values(value))
    return sorted(set(findings))


def _source_attribution_findings(story: Any) -> list[str]:
    findings = []
    for slide in story.presentation.slides:
        for index, source in enumerate(slide.sources):
            if source.evidence or source.url or source.local_reference:
                if not source.license:
                    findings.append(f"slides[{slide.slide_number - 1}].sources[{index}] has no license")
                if not source.owner:
                    findings.append(
                        f"slides[{slide.slide_number - 1}].sources[{index}] has no owner attribution"
                    )
    return findings


def _prepare_output(output_dir: Path, contribution_id: str, overwrite: bool) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    deck = output_dir / f"{contribution_id}.pptx"
    report = output_dir / f"{contribution_id}.validation.json"
    existing = [path for path in (deck, report) if path.exists()]
    if existing and not overwrite:
        raise ValueError("Contribution validation output exists; use --overwrite for these known artifacts.")
    return deck, report


def validate_contribution(
    manifest_path: str | Path,
    output_dir: str | Path,
    *,
    overwrite: bool = False,
) -> dict[str, object]:
    """Validate, render, and report one public contribution without network access."""
    manifest_source = Path(manifest_path).expanduser().resolve()
    manifest_text = manifest_source.read_text(encoding="utf-8")
    manifest = ContributionManifest.model_validate(
        json.loads(manifest_text, object_pairs_hook=_reject_duplicate_keys)
    )
    root = manifest_source.parent.resolve()
    content = (root / manifest.content_path).resolve()
    if not content.is_relative_to(root) or not content.is_file():
        raise ValueError("Contribution content must resolve to a file beside the manifest.")
    raw_text = content.read_text(encoding="utf-8")
    privacy = privacy_findings(manifest_text) + privacy_findings(raw_text)
    if privacy:
        raise ValueError("Privacy validation failed: " + "; ".join(privacy))

    story, migrated = read_story_or_presentation(content)
    attribution = _source_attribution_findings(story)
    if attribution:
        raise ValueError("License/attribution validation failed: " + "; ".join(attribution))

    destination = Path(output_dir).expanduser().resolve()
    deck_path, report_path = _prepare_output(destination, manifest.id, overwrite)
    create_presentation(
        story.presentation.model_dump(mode="json"),
        deck_path,
        asset_root=content.parent,
    )
    if not deck_path.is_file() or deck_path.read_bytes()[:2] != b"PK":
        raise ValueError("Rendering validation did not produce a readable PPTX package.")
    doctor = diagnose_story(story)
    layout = analyze_overflow(story.presentation.model_dump(mode="json"), load_layout_contract())
    report: dict[str, object] = {
        "schema_version": "1",
        "status": "valid",
        "contribution": manifest.model_dump(mode="json"),
        "checks": {
            "privacy": {"status": "passed", "network": "none", "findings": []},
            "license": {"status": "passed", "value": manifest.license},
            "schema": {
                "status": "passed",
                "story_schema": story.schema_version,
                "input_format": "presentation-v1" if migrated else "story-v2",
            },
            "rendering": {
                "status": "passed",
                "pptx": deck_path.name,
                "pptx_sha256": digest_file(deck_path),
                "layout_status": layout["status"],
                "overflow_findings": layout["findings"],
            },
            "attribution": {
                "status": "passed",
                "value": manifest.attribution,
                "assets": len(story.presentation.assets),
                "sources": sum(len(slide.sources) for slide in story.presentation.slides),
            },
        },
        "doctor": {"status": doctor["status"], "summary": doctor["summary"]},
        "disclaimer": (
            "Validation checks public contribution boundaries; it does not verify factual truth, "
            "permission claims, or every possible secret format."
        ),
    }
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    return report
