import json
from pathlib import Path

from pptx import Presentation

from storyboard_studio.cli import main
from storyboard_studio.resources import web_root


def test_packaged_web_application_is_complete():
    root = web_root()
    assert (root / "index.html").is_file()
    assert (root / "static" / "app.js").is_file()
    assert (root / "static" / "app.css").is_file()
    assert (root / "static" / "favicon.svg").is_file()
    package_root = root.parent
    assert (package_root / "data" / "storyboard-v1.json").is_file()
    assert (package_root / "data" / "story-v2.json").is_file()
    assert (package_root / "data" / "decision-brief.story.json").is_file()


def test_demo_and_export_commands_create_editable_powerpoints(tmp_path: Path):
    demo = tmp_path / "demo.pptx"
    exported = tmp_path / "exported.pptx"

    assert main(["demo", "--output", str(demo)]) == 0
    assert (
        main(
            [
                "export",
                "--input",
                "examples/product-brief.json",
                "--output",
                str(exported),
            ]
        )
        == 0
    )

    assert len(Presentation(demo).slides) == 6
    assert len(Presentation(exported).slides) == 4


def test_doctor_command_writes_stable_json(tmp_path: Path):
    output = tmp_path / "doctor.json"
    assert (
        main(
            [
                "doctor",
                "examples/product-brief.json",
                "--format",
                "json",
                "--output",
                str(output),
            ]
        )
        == 0
    )

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["schema_version"] == "1"
    assert report["summary"]["slides"] == 3
    assert "does not verify factual truth" in report["disclaimer"]


def test_compile_command_creates_versioned_decision_story(tmp_path: Path):
    output = tmp_path / "decision.story.json"
    assert (
        main(
            [
                "compile",
                "--input",
                "examples/briefs/onboarding-decision.json",
                "--output",
                str(output),
                "--theme",
                "forest",
            ]
        )
        == 0
    )
    story = json.loads(output.read_text(encoding="utf-8"))
    assert story["schema_version"] == "2"
    assert story["kind"] == "decision-brief"
    assert story["presentation"]["theme"] == "forest"
