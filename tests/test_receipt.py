import json
from pathlib import Path

from pptx import Presentation

from storyboard_studio.cli import main
from storyboard_studio.receipt import diff_stories, verify_receipt
from storyboard_studio.story import read_story_or_presentation


def test_bundle_receipt_verifies_and_detects_tampering(tmp_path: Path):
    output = tmp_path / "deck.pptx"
    assert (
        main(
            [
                "export",
                "--input",
                "examples/product-brief.json",
                "--output",
                str(output),
                "--bundle",
                "--viewer-status",
                "LibreOffice 26.8: opened and editable",
            ]
        )
        == 0
    )
    story_path = tmp_path / "deck.story.json"
    receipt_path = tmp_path / "deck.receipt.json"
    assert output.is_file()
    assert story_path.is_file()
    assert receipt_path.is_file()
    assert verify_receipt(receipt_path)["status"] == "verified"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["viewer_status"] == "LibreOffice 26.8: opened and editable"
    assert "outline sha256" in Presentation(output).core_properties.comments

    story_path.write_text("{}\n", encoding="utf-8")
    result = verify_receipt(receipt_path)
    assert result["status"] == "invalid"
    assert any("digest mismatch" in error for error in result["errors"])


def test_diff_requires_and_reports_versioned_story_changes(tmp_path: Path):
    first = tmp_path / "first.story.json"
    second = tmp_path / "second.story.json"
    assert main(["migrate", "examples/product-brief.json", "--output", str(first)]) == 0
    story = json.loads(first.read_text(encoding="utf-8"))
    story["presentation"]["title"] = "A changed review title"
    second.write_text(json.dumps(story), encoding="utf-8")

    old, _ = read_story_or_presentation(first)
    new, _ = read_story_or_presentation(second)
    report = diff_stories(old, new)

    assert report["changed"] is True
    assert any(change["path"] == "presentation.title" for change in report["changes"])


def test_receipt_records_checksum_license_attribution_and_alt_text_for_local_assets(
    tmp_path: Path,
):
    output = tmp_path / "native-visuals.pptx"
    assert (
        main(
            [
                "export",
                "--input",
                "assets/demo/native-visuals.json",
                "--output",
                str(output),
                "--bundle",
                "--viewer-status",
                "LibreOffice 26.8: native charts and image rendered",
            ]
        )
        == 0
    )
    receipt = json.loads((tmp_path / "native-visuals.receipt.json").read_text(encoding="utf-8"))

    assert receipt["source_coverage"]["local_assets"] == 2
    assert [asset["id"] for asset in receipt["asset_provenance"]] == [
        "pilot-results",
        "decision-flow",
    ]
    assert receipt["asset_provenance"][1]["license"] == "CC0-1.0"
    assert "local brief moves through diagnosis" in receipt["asset_provenance"][1]["alt_text"].lower()
    assert verify_receipt(tmp_path / "native-visuals.receipt.json")["status"] == "verified"


def test_checked_in_gallery_receipts_survive_model_defaults():
    for path in Path("tests/fixtures/receipts-v1").glob("*/deck.receipt.json"):
        result = verify_receipt(path)
        assert result["status"] == "verified", (path, result)
        assert result["scope"] == "legacy-artifact-integrity"
        assert "doctor" in result["unverified_fields"]


def test_receipt_rejects_changed_derived_metadata(tmp_path: Path):
    main(["demo", "--bundle", "--output", str(tmp_path / "deck.pptx")])
    path = tmp_path / "deck.receipt.json"
    original = json.loads(path.read_text())
    for field, altered in [
        ("doctor", {"status": "fabricated"}),
        ("source_coverage", {"claims": 999999}),
        ("planner", "forged"),
        ("source_provenance", []),
        ("unresolved_gaps", []),
    ]:
        receipt = {**original, field: altered}
        path.write_text(json.dumps(receipt))
        result = verify_receipt(path)
        assert result["status"] == "invalid", (field, result)
        assert any(field in error for error in result["errors"])


def test_receipt_reports_malformed_input_without_traceback(tmp_path: Path):
    path = tmp_path / "bad.receipt.json"
    for content in ["{", "[]", "null", "42", '{"schema_version":"unknown"}']:
        path.write_text(content)
        assert verify_receipt(path)["status"] == "invalid"
    assert verify_receipt(tmp_path / "missing.json")["status"] == "invalid"


def test_receipt_rejects_unsupported_contract_and_escaping_paths(tmp_path: Path):
    main(["demo", "--bundle", "--output", str(tmp_path / "deck.pptx")])
    path = tmp_path / "deck.receipt.json"
    original = json.loads(path.read_text())
    receipt = {**original, "canonicalization": "unknown"}
    path.write_text(json.dumps(receipt))
    assert verify_receipt(path)["status"] == "invalid"
    receipt = json.loads(json.dumps(original))
    receipt["artifacts"]["story"]["path"] = str(tmp_path / "deck.story.json")
    path.write_text(json.dumps(receipt))
    assert verify_receipt(path)["status"] == "invalid"


def test_current_gallery_has_three_verified_bundles():
    receipts = list(Path("gallery").glob("*/deck.receipt.json"))
    assert len(receipts) == 3
    for path in receipts:
        result = verify_receipt(path)
        assert result["status"] == "verified", (path, result)
        assert result["scope"] == "artifacts-and-derived-metadata"
