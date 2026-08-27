from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

from schemas import DecisionBriefV2
from storyboard_studio.cli import main as cli_main
from storyboard_studio.story import build_decision_story
from storyboard_studio.tool_server import MAX_REQUEST_BYTES, ToolServer, serve_stdio


def _brief() -> DecisionBriefV2:
    return DecisionBriefV2.model_validate_json(
        Path("examples/briefs/onboarding-decision.json").read_text(encoding="utf-8")
    )


def _request(action: str, arguments: dict[str, object] | None = None, request_id: str = "1"):
    return {"id": request_id, "action": action, "arguments": arguments or {}}


def test_capabilities_are_machine_readable_and_publish_hard_boundaries(tmp_path: Path):
    server = ToolServer(tmp_path, Path("artifacts"))
    response = server.handle(_request("capabilities"))

    assert response["ok"] is True
    result = response["result"]
    assert result["transport"] == "jsonl-stdio"
    assert result["network"] == "none"
    assert set(result["actions"]) == {
        "capabilities",
        "create_draft",
        "diagnose",
        "diff",
        "render",
        "verify",
    }
    assert result["unsupported"]["review_bypass"] is True
    assert result["limits"]["max_request_bytes"] == MAX_REQUEST_BYTES
    assert result["review"]["factual_truth_verified"] is False


def test_create_diagnose_and_diff_use_the_canonical_story_models(tmp_path: Path):
    server = ToolServer(tmp_path, Path("artifacts"))
    created = server.handle(
        _request("create_draft", {"brief": _brief().model_dump(mode="json"), "theme": "forest"})
    )

    assert created["ok"] is True
    story = created["result"]["story"]
    assert story["schema_version"] == "2"
    assert story["presentation"]["theme"] == "forest"
    assert created["result"]["review"]["factual_truth_verified"] is False

    diagnosed = server.handle(_request("diagnose", {"story": story}, "2"))
    assert diagnosed["ok"] is True
    assert diagnosed["result"]["diagnosis"]["story_kind"] == "decision-brief"

    changed = json.loads(json.dumps(story))
    changed["presentation"]["title"] = "A reviewed title change"
    diffed = server.handle(_request("diff", {"old_story": story, "new_story": changed}, "3"))
    assert diffed["ok"] is True
    assert diffed["result"]["diff"]["changed"] is True
    assert diffed["result"]["factual_truth_verified"] is False


def test_unsupported_provider_and_action_have_stable_error_codes(tmp_path: Path):
    server = ToolServer(tmp_path, Path("artifacts"))
    provider = server.handle(
        _request(
            "create_draft",
            {"brief": _brief().model_dump(mode="json"), "provider": "gemini"},
        )
    )
    unknown = server.handle(_request("research_the_web"))

    assert provider["error"]["code"] == "unsupported-provider"
    assert provider["error"]["data"]["supported_providers"] == ["local"]
    assert unknown["error"]["code"] == "unsupported-action"
    assert "render" in unknown["error"]["data"]["supported_actions"]


def test_render_requires_review_acknowledgement_and_never_overwrites(tmp_path: Path):
    server = ToolServer(tmp_path, Path("artifacts"))
    story = build_decision_story(_brief()).model_dump(mode="json")
    blocked = server.handle(_request("render", {"story": story, "filename": "review.pptx"}))

    assert blocked["ok"] is False
    assert blocked["error"]["code"] == "review-required"
    assert blocked["error"]["data"]["review"]["canonical_surface"] == "browser-studio"

    rendered = server.handle(
        _request(
            "render",
            {
                "story": story,
                "filename": "review.pptx",
                "acknowledge_review_warnings": True,
            },
            "2",
        )
    )
    assert rendered["ok"] is True
    assert (tmp_path / "artifacts" / "review.pptx").read_bytes()[:2] == b"PK"
    assert rendered["result"]["artifact"]["path"] == "artifacts/review.pptx"
    assert len(rendered["result"]["artifact"]["sha256"]) == 64

    repeated = server.handle(
        _request(
            "render",
            {
                "story": story,
                "filename": "review.pptx",
                "acknowledge_review_warnings": True,
            },
            "3",
        )
    )
    assert repeated["error"]["code"] == "artifact-exists"


def test_verify_is_confined_to_workspace_and_checks_real_receipt(tmp_path: Path):
    source = tmp_path / "source.json"
    source.write_text(Path("examples/product-brief.json").read_text(encoding="utf-8"), encoding="utf-8")
    deck = tmp_path / "deck.pptx"
    assert cli_main(["export", "--input", str(source), "--output", str(deck), "--bundle"]) == 0
    server = ToolServer(tmp_path, Path("tool-output"))

    verified = server.handle(_request("verify", {"receipt_path": "deck.receipt.json"}))
    escaped = server.handle(_request("verify", {"receipt_path": "../private.receipt.json"}, "2"))

    assert verified["ok"] is True
    assert verified["result"]["verification"]["status"] == "verified"
    assert escaped["ok"] is False
    assert escaped["error"]["code"] == "filesystem-boundary"


def test_jsonl_stdio_and_installed_cli_once_mode(tmp_path: Path):
    server = ToolServer(tmp_path, Path("artifacts"))
    stdin = io.BytesIO((json.dumps(_request("capabilities")) + "\n").encode())
    stdout = io.StringIO()
    assert serve_stdio(server, once=True, stdin=stdin, stdout=stdout) == 0
    assert json.loads(stdout.getvalue())["result"]["network"] == "none"

    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "storyboard_studio.cli",
            "tools",
            "--workspace",
            str(tmp_path),
            "--output-dir",
            "cli-output",
            "--once",
        ],
        input=json.dumps(_request("capabilities")) + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert process.returncode == 0
    assert json.loads(process.stdout)["result"]["server"] == "storyboard-tools"
