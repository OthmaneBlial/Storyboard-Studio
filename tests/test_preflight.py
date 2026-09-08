import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import server
from ai_helper import build_local_presentation
from generate_pptx import create_presentation
from schemas import PresentationPayload
from storyboard_studio.cli import main
from storyboard_studio.preflight import ExportPreflightError
from storyboard_studio.projects import ProjectPayload, write_project
from storyboard_studio.story import migrate_presentation_v1
from storyboard_studio.tool_server import ToolServer


def overflow_story():
    raw = build_local_presentation("Choose a shared support queue", 3)
    raw["slides"][0]["title"] = "A" * 65
    raw["slides"][0]["layout"] = "right"
    return migrate_presentation_v1(PresentationPayload.model_validate(raw))


def test_renderer_and_project_bundle_block_the_same_overflow_without_output(tmp_path):
    story = overflow_story()
    for output, render in [
        (
            tmp_path / "direct.pptx",
            lambda output: create_presentation(story.presentation.model_dump(), output),
        ),
        (
            tmp_path / "bundle.zip",
            lambda output: write_project(ProjectPayload(story=story), output, render=True),
        ),
    ]:
        with pytest.raises(ExportPreflightError) as failure:
            render(output)
        assert failure.value.report["findings"][0]["path"] == "slides.0.title"
        assert not output.exists()
    # Saving editable inputs remains possible so the author can repair them.
    write_project(ProjectPayload(story=story), tmp_path / "editable.zip")
    assert (tmp_path / "editable.zip").is_file()


def test_all_http_export_routes_share_findings_and_discard_failed_directories(tmp_path, monkeypatch):
    story = overflow_story()
    cache = tmp_path / "cache"
    monkeypatch.setattr(server, "OUTPUT_DIR", cache)
    server._requests.clear()
    expected = None
    with TestClient(server.app, base_url="http://127.0.0.1") as client:
        for route, payload in [
            ("/api/presentations", {"presentation": story.presentation.model_dump(mode="json")}),
            ("/api/v1/presentations", {"presentation": story.presentation.model_dump(mode="json")}),
            ("/api/v1/bundles", story.model_dump(mode="json")),
            ("/api/v1/projects/export", {"story": story.model_dump(mode="json")}),
            ("/api/v1/projects/bundle", {"story": story.model_dump(mode="json")}),
        ]:
            response = client.post(route, json=payload)
            assert response.status_code == 422, (route, response.text)
            findings = response.json()["findings"]
            if expected is None:
                expected = findings
            assert findings == expected
            assert list(cache.iterdir()) == []


def test_cli_and_jsonl_cannot_bypass_layout_gate_by_acknowledging_doctor(tmp_path, capsys):
    story = overflow_story()
    source = tmp_path / "source.json"
    source.write_text(json.dumps(story.model_dump(mode="json")))
    output = tmp_path / "result.pptx"
    with pytest.raises(SystemExit) as failure:
        main(["export", "--input", str(source), "--output", str(output), "--bundle"])
    assert failure.value.code == 2
    assert "Export preflight failed" in capsys.readouterr().err
    assert not output.exists()
    assert not output.with_suffix(".story.json").exists()
    tool = ToolServer(tmp_path, Path("tools"))
    response = tool.handle(
        {
            "id": "overflow",
            "action": "render",
            "arguments": {
                "story": story.model_dump(mode="json"),
                "filename": "tool.pptx",
                "acknowledge_review_warnings": True,
            },
        }
    )
    assert response["ok"] is False
    assert response["error"]["code"] == "export-preflight"
    assert list((tmp_path / "tools").iterdir()) == []
