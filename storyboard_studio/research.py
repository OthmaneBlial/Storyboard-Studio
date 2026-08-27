"""Privacy-safe validation and aggregation for consented user research records.

Research records are deliberately a separate contract from product stories.  The
module accepts only anonymised timing, outcome, friction, and (optionally)
permissioned quote fields; it never reads a brief, deck, screenshot, or source
file.  Raw records should stay outside the repository.  The aggregate output is
safe to publish only after the researcher has reviewed it.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path
from statistics import median
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from storyboard_studio.contributions import privacy_findings

FRICTION_CODES = (
    "setup-abandonment",
    "install-ambiguity",
    "generic-output",
    "doctor-false-positive",
    "evidence-friction",
    "preview-confusion",
    "export-confusion",
    "viewer-mismatch",
    "other",
)
AUDIENCE_BANDS = ("product-ops", "consulting-enablement", "developer-automation")
WORKFLOWS = ("golden-synthetic", "real-private-content-not-collected")
MAX_SECONDS = 86_400

FrictionCode = Literal[
    "setup-abandonment",
    "install-ambiguity",
    "generic-output",
    "doctor-false-positive",
    "evidence-friction",
    "preview-confusion",
    "export-confusion",
    "viewer-mismatch",
    "other",
]
AudienceBand = Literal["product-ops", "consulting-enablement", "developer-automation"]
ResearchWorkflow = Literal["golden-synthetic", "real-private-content-not-collected"]


class ResearchModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class OutcomeTiming(ResearchModel):
    outcome: Literal["completed", "abandoned"]
    seconds: int = Field(ge=0, le=MAX_SECONDS)


class ExportTiming(ResearchModel):
    outcome: Literal["completed", "abandoned"]
    total_seconds: int = Field(ge=0, le=MAX_SECONDS)
    viewer: str = Field(min_length=1, max_length=120)


class DoctorFeedback(ResearchModel):
    useful_codes: list[FrictionCode] = Field(default_factory=list, max_length=9)
    false_positive_codes: list[FrictionCode] = Field(default_factory=list, max_length=9)

    @model_validator(mode="after")
    def codes_are_unique(self) -> DoctorFeedback:
        for field_name, values in (
            ("useful_codes", self.useful_codes),
            ("false_positive_codes", self.false_positive_codes),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must contain unique friction codes.")
        return self


class QuoteRecord(ResearchModel):
    permission: Literal["no", "yes"] = "no"
    text: str = Field(default="", max_length=240)

    @model_validator(mode="after")
    def permission_matches_text(self) -> QuoteRecord:
        if self.permission == "no" and self.text:
            raise ValueError("A quote must be empty when publication permission is no.")
        if self.permission == "yes" and not self.text:
            raise ValueError("A permissioned quote must contain anonymised text.")
        return self


class ResearchSession(ResearchModel):
    schema_version: Literal["1"] = "1"
    session_id: str = Field(pattern=r"^S[0-9]{2,}$")
    consent: Literal["yes"] = "yes"
    consent_date: date
    audience_band: AudienceBand
    workflow: ResearchWorkflow
    setup: OutcomeTiming
    first_editable_story_seconds: int = Field(ge=0, le=MAX_SECONDS)
    export: ExportTiming
    friction_codes: list[FrictionCode] = Field(default_factory=list, max_length=9)
    doctor: DoctorFeedback = Field(default_factory=DoctorFeedback)
    evidence_friction: str = Field(default="none", min_length=1, max_length=240)
    interventions: int = Field(default=0, ge=0, le=100)
    outcome: str = Field(min_length=1, max_length=240)
    quote: QuoteRecord = Field(default_factory=QuoteRecord)

    @field_validator("friction_codes")
    @classmethod
    def friction_codes_are_unique(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)):
            raise ValueError("friction_codes must contain unique friction codes.")
        return values

    @model_validator(mode="after")
    def real_workflow_requires_no_collected_content(self) -> ResearchSession:
        if self.workflow == "real-private-content-not-collected" and any(
            marker in self.outcome.lower()
            for marker in ("brief:", "deck:", "source:", "company:", "employer:")
        ):
            raise ValueError("Real workflow outcomes must remain short and anonymised.")
        if self.setup.outcome == "completed" and self.setup.seconds == 0:
            raise ValueError("A completed setup must have a positive duration.")
        if self.export.outcome == "completed" and self.export.total_seconds == 0:
            raise ValueError("A completed export must have a positive duration.")
        return self


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key {key!r} is not allowed.")
        result[key] = value
    return result


def _load_json(path: Path) -> tuple[ResearchSession, str]:
    raw = path.read_text(encoding="utf-8")
    try:
        value = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
        session = ResearchSession.model_validate(value)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"Invalid research session {path}: {exc}") from exc
    findings = privacy_findings(raw)
    if findings:
        raise ValueError(f"Research privacy validation failed for {path}: {'; '.join(findings)}")
    return session, raw


def load_research_session(path: str | Path) -> ResearchSession:
    """Load one strict, anonymised session record without network access."""

    session, _ = _load_json(Path(path).expanduser().resolve())
    return session


def validate_research_session(path: str | Path) -> dict[str, object]:
    """Validate one private session and return a machine-readable local report."""

    source = Path(path).expanduser().resolve()
    session, _ = _load_json(source)
    return {
        "schema_version": "1",
        "status": "valid",
        "network": "none",
        "source": source.name,
        "session": session.model_dump(mode="json"),
        "checks": {
            "consent": "yes",
            "private_content": "not_collected_by_contract",
            "privacy_scan": "passed",
        },
        "disclaimer": (
            "Validation checks the declared anonymised record shape and high-confidence privacy patterns; "
            "it cannot prove that a researcher followed the collection protocol."
        ),
    }


def _prepare_output(output_dir: Path, overwrite: bool) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "aggregate.json"
    markdown_path = output_dir / "aggregate.md"
    existing = [path for path in (json_path, markdown_path) if path.exists()]
    if existing and not overwrite:
        raise ValueError("Research aggregate output exists; use --overwrite for these known artifacts.")
    return json_path, markdown_path


def _median_seconds(values: list[int]) -> int | None:
    return int(median(values)) if values else None


def _public_audience_mix(sessions: list[ResearchSession]) -> dict[str, int]:
    counts = Counter(session.audience_band for session in sessions)
    return {band: counts[band] for band in AUDIENCE_BANDS if counts[band] >= 3}


def _markdown_report(report: dict[str, object]) -> str:
    summary = report["summary"]
    assert isinstance(summary, dict)
    completion = summary["completion"]
    assert isinstance(completion, dict)
    friction = report["friction_codes"]
    assert isinstance(friction, dict)
    lines = [
        "# User research aggregate",
        "",
        "> This report contains only consented timing, friction, outcome, and explicitly permissioned "
        "anonymised quotes. It does not prove factual truth or replace researcher review.",
        "",
        f"- Valid sessions: **{summary['sessions']}**",
        f"- Real private workflows observed: **{summary['real_private_workflows']}**",
        f"- Setup completion: **{completion['setup_completed']} / {summary['sessions']}**",
        f"- Export completion: **{completion['export_completed']} / {summary['sessions']}**",
        f"- Median first editable story: **{summary['median_first_editable_story_seconds']} seconds**",
        f"- Median usable export: **{summary['median_export_seconds']} seconds**",
        "",
        "## Friction",
        "",
    ]
    if friction:
        lines.extend(f"- `{code}`: {count}" for code, count in friction.items())
    else:
        lines.append("- None reported")
    lines.extend(
        [
            "",
            "## Decisions",
            "",
            f"- Second-template decision: {report['second_template_decision']}",
            f"- Product-thesis decision: {report['product_thesis_decision']}",
            "",
            "## Permissioned quotes",
            "",
        ]
    )
    quotes = report["permissioned_quotes"]
    assert isinstance(quotes, list)
    lines.extend(f"> {quote}" for quote in quotes) if quotes else lines.append("None")
    lines.append("")
    return "\n".join(lines)


def aggregate_research_sessions(
    input_dir: str | Path,
    output_dir: str | Path,
    *,
    overwrite: bool = False,
) -> dict[str, object]:
    """Aggregate validated local records without copying raw session content."""

    source = Path(input_dir).expanduser().resolve()
    if not source.is_dir():
        raise ValueError(f"Research input directory does not exist: {source}")
    paths = sorted(
        path
        for path in source.glob("*.json")
        if path.name != "aggregate.json" and not path.name.endswith(".validation.json")
    )
    if not paths:
        raise ValueError("Research input directory contains no JSON session records.")
    sessions = [load_research_session(path) for path in paths]
    ids = [session.session_id for session in sessions]
    if len(ids) != len(set(ids)):
        raise ValueError("Research session_id values must be unique.")

    friction_counts = Counter(code for session in sessions for code in session.friction_codes)
    friction_counts.update(code for session in sessions for code in session.doctor.false_positive_codes)
    setup_completed = sum(session.setup.outcome == "completed" for session in sessions)
    export_completed = sum(session.export.outcome == "completed" for session in sessions)
    first_story_times = [
        session.first_editable_story_seconds
        for session in sessions
        if session.first_editable_story_seconds > 0
    ]
    export_times = [
        session.export.total_seconds
        for session in sessions
        if session.export.outcome == "completed" and session.export.total_seconds > 0
    ]
    real_workflows = sum(session.workflow == "real-private-content-not-collected" for session in sessions)
    permissioned_quotes = [session.quote.text for session in sessions if session.quote.permission == "yes"]
    report: dict[str, object] = {
        "schema_version": "1",
        "status": "valid",
        "network": "none",
        "summary": {
            "sessions": len(sessions),
            "real_private_workflows": real_workflows,
            "median_first_editable_story_seconds": _median_seconds(first_story_times),
            "median_export_seconds": _median_seconds(export_times),
            "completion": {
                "setup_completed": setup_completed,
                "export_completed": export_completed,
            },
        },
        "audience_mix": _public_audience_mix(sessions),
        "suppressed_audience_bands": [
            band for band in AUDIENCE_BANDS if band not in _public_audience_mix(sessions)
        ],
        "friction_codes": dict(sorted(friction_counts.items())),
        "doctor_false_positive_count": sum(len(session.doctor.false_positive_codes) for session in sessions),
        "evidence_friction_count": sum(session.evidence_friction.lower() != "none" for session in sessions),
        "permissioned_quotes": permissioned_quotes,
        "validated_session_ids": ids,
        "second_template_decision": (
            "eligible for evidence review"
            if len(sessions) >= 10 and real_workflows >= 5
            else "deferred pending 10 consented sessions and 5 real workflows"
        ),
        "product_thesis_decision": (
            "review against observed evidence"
            if len(sessions) >= 10 and real_workflows >= 5
            else "deferred pending 10 consented sessions and 5 real workflows"
        ),
        "disclaimer": (
            "This aggregate contains declared anonymised research records only. It does not prove that "
            "participants were representative, that quotes are factual, or that the product is useful."
        ),
    }
    destination = Path(output_dir).expanduser().resolve()
    json_path, markdown_path = _prepare_output(destination, overwrite)
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(_markdown_report(report), encoding="utf-8")
    return report


__all__ = [
    "ResearchSession",
    "aggregate_research_sessions",
    "load_research_session",
    "validate_research_session",
]
