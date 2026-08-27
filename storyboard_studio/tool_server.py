"""Agent-neutral local JSONL tool server for stable review actions."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Literal, TextIO

from pydantic import Field, ValidationError, field_validator

from generate_pptx import create_presentation
from schemas import DecisionBriefV2, StoryDocumentV2, StrictModel
from storyboard_studio import __version__
from storyboard_studio.doctor import diagnose_story
from storyboard_studio.evidence import evidence_coverage
from storyboard_studio.receipt import diff_stories, digest_file, digest_value, verify_receipt
from storyboard_studio.story import build_decision_story

PROTOCOL_VERSION = "1"
MAX_REQUEST_BYTES = 200_000
ARTIFACT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}\.pptx$")
THEMES = Literal["midnight", "glacier", "ember", "forest", "royal", "sakura"]


class CreateDraftArguments(StrictModel):
    brief: DecisionBriefV2
    theme: THEMES = "midnight"
    provider: Literal["local"] = "local"


class DiagnoseArguments(StrictModel):
    story: StoryDocumentV2


class DiffArguments(StrictModel):
    old_story: StoryDocumentV2
    new_story: StoryDocumentV2


class RenderArguments(StrictModel):
    story: StoryDocumentV2
    filename: str = Field(default="reviewed-story.pptx", min_length=6, max_length=105)
    acknowledge_review_warnings: bool = False

    @field_validator("filename")
    @classmethod
    def safe_artifact_name(cls, value: str) -> str:
        if not ARTIFACT_RE.fullmatch(value):
            raise ValueError("filename must be one safe .pptx basename without directories")
        return value


class VerifyArguments(StrictModel):
    receipt_path: str = Field(min_length=1, max_length=240)


class ToolProtocolError(Exception):
    def __init__(self, code: str, message: str, data: dict[str, object] | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data or {}


def _validation_details(error: ValidationError) -> list[dict[str, object]]:
    return [
        {"path": ".".join(str(item) for item in issue["loc"]), "message": issue["msg"], "type": issue["type"]}
        for issue in error.errors(include_input=False)
    ]


def _review_state(story: StoryDocumentV2) -> dict[str, object]:
    doctor = diagnose_story(story)
    evidence = evidence_coverage(story.presentation)
    open_findings = doctor["summary"]["open_findings"]
    unresolved_claims = evidence["summary"]["unresolved_claims"]
    return {
        "required": bool(open_findings or unresolved_claims),
        "canonical_surface": "browser-studio",
        "browser_command": "storyboard serve",
        "doctor_status": doctor["status"],
        "doctor_summary": doctor["summary"],
        "evidence_summary": evidence["summary"],
        "warning_codes": [finding["code"] for finding in doctor["findings"]],
        "factual_truth_verified": False,
        "disclaimer": (
            "Schema and integrity checks do not verify factual truth; a human author owns review."
        ),
    }


def capability_metadata(workspace: Path, output_dir: Path) -> dict[str, object]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "server": "storyboard-tools",
        "version": __version__,
        "transport": "jsonl-stdio",
        "network": "none",
        "provider": "local-only",
        "actions": {
            "capabilities": {"status": "supported", "arguments": []},
            "create_draft": {
                "status": "supported",
                "arguments": ["brief", "theme", "provider=local"],
            },
            "diagnose": {"status": "supported", "arguments": ["story"]},
            "diff": {"status": "supported", "arguments": ["old_story", "new_story"]},
            "render": {
                "status": "supported",
                "arguments": ["story", "filename", "acknowledge_review_warnings"],
                "review_gate": True,
            },
            "verify": {"status": "supported", "arguments": ["receipt_path"]},
        },
        "unsupported": {
            "network_providers": ["gemini", "openai-compatible"],
            "file_ingestion": ["docx", "pdf"],
            "factual_verification": True,
            "review_bypass": True,
        },
        "limits": {
            "max_request_bytes": MAX_REQUEST_BYTES,
            "rate": "sequential stdio; one response per request line",
            "retention": "requests and responses are not retained",
            "filesystem_workspace": str(workspace),
            "filesystem_output": str(output_dir),
            "render_overwrite": False,
        },
        "review": {
            "canonical_surface": "browser-studio",
            "command": "storyboard serve",
            "factual_truth_verified": False,
        },
    }


class ToolServer:
    def __init__(self, workspace: Path, output_dir: Path):
        self.workspace = workspace.expanduser().resolve()
        if not self.workspace.is_dir():
            raise ValueError("Tool workspace must be an existing directory")
        candidate = output_dir if output_dir.is_absolute() else self.workspace / output_dir
        self.output_dir = self._inside(candidate, "Output directory")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _inside(self, candidate: Path, label: str) -> Path:
        resolved = candidate.expanduser().resolve()
        try:
            resolved.relative_to(self.workspace)
        except ValueError as exc:
            raise ValueError(f"{label} must stay inside the configured workspace") from exc
        return resolved

    def _receipt_path(self, value: str) -> Path:
        candidate = Path(value)
        if candidate.is_absolute():
            raise ToolProtocolError("filesystem-boundary", "receipt_path must be workspace-relative")
        try:
            resolved = self._inside(self.workspace / candidate, "Receipt path")
        except ValueError as exc:
            raise ToolProtocolError(
                "filesystem-boundary", "Receipt path must stay inside the configured workspace"
            ) from exc
        if resolved.is_symlink() or not resolved.is_file():
            raise ToolProtocolError("receipt-not-found", "Receipt must be one existing non-symlink file")
        return resolved

    def capabilities(self) -> dict[str, object]:
        return capability_metadata(self.workspace, self.output_dir)

    def _dispatch(self, action: str, arguments: dict[str, object]) -> dict[str, object]:
        if action == "capabilities":
            if arguments:
                raise ToolProtocolError("invalid-arguments", "capabilities does not accept arguments")
            return self.capabilities()
        if action == "create_draft":
            if arguments.get("provider", "local") != "local":
                raise ToolProtocolError(
                    "unsupported-provider",
                    "The tool server supports deterministic local draft creation only.",
                    {"supported_providers": ["local"]},
                )
            parsed = CreateDraftArguments.model_validate(arguments)
            story = build_decision_story(parsed.brief, parsed.theme)
            return {"story": story.model_dump(mode="json"), "review": _review_state(story)}
        if action == "diagnose":
            parsed = DiagnoseArguments.model_validate(arguments)
            return {"diagnosis": diagnose_story(parsed.story), "review": _review_state(parsed.story)}
        if action == "diff":
            parsed = DiffArguments.model_validate(arguments)
            return {
                "diff": diff_stories(parsed.old_story, parsed.new_story),
                "factual_truth_verified": False,
            }
        if action == "render":
            parsed = RenderArguments.model_validate(arguments)
            review = _review_state(parsed.story)
            if review["required"] and not parsed.acknowledge_review_warnings:
                raise ToolProtocolError(
                    "review-required",
                    "Open the canonical browser review surface or explicitly acknowledge current warnings.",
                    {"review": review},
                )
            destination = self._inside(self.output_dir / parsed.filename, "Render artifact")
            if destination.exists() or destination.is_symlink():
                raise ToolProtocolError("artifact-exists", "Render refuses to overwrite an existing artifact")
            provenance = (
                f"Storyboard Studio tool server {__version__}; story schema {parsed.story.schema_version}; "
                f"outline sha256 {digest_value(parsed.story.presentation.model_dump(mode='json'))}; "
                "factual truth not verified."
            )
            create_presentation(
                parsed.story.presentation.model_dump(),
                destination,
                provenance=provenance,
                asset_root=self.workspace,
            )
            return {
                "artifact": {
                    "path": destination.relative_to(self.workspace).as_posix(),
                    "sha256": digest_file(destination),
                    "media_type": (
                        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                    ),
                },
                "review": review,
            }
        if action == "verify":
            parsed = VerifyArguments.model_validate(arguments)
            return {"verification": verify_receipt(self._receipt_path(parsed.receipt_path))}
        raise ToolProtocolError(
            "unsupported-action",
            f"Action {action!r} is not supported.",
            {"supported_actions": list(self.capabilities()["actions"])},
        )

    def handle(self, request: object) -> dict[str, object]:
        request_id: object = None
        try:
            if not isinstance(request, dict):
                raise ToolProtocolError("invalid-request", "Request must be one JSON object")
            request_id = request.get("id")
            if not isinstance(request_id, str | int) or isinstance(request_id, bool):
                raise ToolProtocolError("invalid-request", "Request id must be a string or integer")
            if set(request) - {"id", "action", "arguments"}:
                raise ToolProtocolError("invalid-request", "Request contains unsupported top-level fields")
            action = request.get("action")
            arguments = request.get("arguments", {})
            if not isinstance(action, str) or not action:
                raise ToolProtocolError("invalid-request", "Request action must be a non-empty string")
            if not isinstance(arguments, dict):
                raise ToolProtocolError("invalid-request", "Request arguments must be one JSON object")
            result = self._dispatch(action, arguments)
            return {
                "protocol_version": PROTOCOL_VERSION,
                "id": request_id,
                "ok": True,
                "result": result,
            }
        except ValidationError as exc:
            error = ToolProtocolError(
                "validation-error",
                "Arguments do not match the canonical Storyboard schema.",
                {"issues": _validation_details(exc)},
            )
        except ToolProtocolError as exc:
            error = exc
        except (OSError, ValueError, json.JSONDecodeError):
            error = ToolProtocolError(
                "operation-failed", "The local operation failed without exposing private details."
            )
        return {
            "protocol_version": PROTOCOL_VERSION,
            "id": request_id,
            "ok": False,
            "error": {"code": error.code, "message": error.message, "data": error.data},
        }


def serve_stdio(
    server: ToolServer,
    *,
    once: bool = False,
    stdin: Any = None,
    stdout: TextIO | None = None,
) -> int:
    input_stream = stdin if stdin is not None else sys.stdin.buffer
    output_stream = stdout if stdout is not None else sys.stdout
    handled = 0
    while True:
        line = input_stream.readline(MAX_REQUEST_BYTES + 1)
        if not line:
            break
        handled += 1
        if isinstance(line, str):
            encoded = line.encode("utf-8")
        else:
            encoded = line
        if len(encoded) > MAX_REQUEST_BYTES or not encoded.endswith(b"\n"):
            response = {
                "protocol_version": PROTOCOL_VERSION,
                "id": None,
                "ok": False,
                "error": {
                    "code": "request-too-large",
                    "message": f"Request must fit on one line below {MAX_REQUEST_BYTES} bytes.",
                    "data": {},
                },
            }
        else:
            try:
                request = json.loads(encoded.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                request = None
            response = server.handle(request)
        output_stream.write(json.dumps(response, ensure_ascii=False, default=str) + "\n")
        output_stream.flush()
        if once:
            break
    return 0 if handled or not once else 1
