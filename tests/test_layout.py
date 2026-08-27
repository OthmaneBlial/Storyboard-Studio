import json
from pathlib import Path

import pytest

from ai_helper import build_local_presentation
from storyboard_studio.layout import (
    LayoutContractError,
    analyze_overflow,
    contrast_ratio,
    load_brand_kit,
    load_layout_contract,
)


def test_runtime_layout_contract_has_accessible_bounded_public_themes():
    contract = load_layout_contract()

    assert contract.schema_version == "2"
    assert contract.canvas.aspect_ratio == "16:9"
    assert set(contract.layouts) == {"left", "right", "focus"}
    assert len(contract.themes) == 6
    assert all(contrast_ratio(theme.text, theme.bg) >= 4.5 for theme in contract.themes.values())
    assert all(stack[-1] == "sans-serif" for stack in contract.font_fallbacks.values())


def test_layout_contract_rejects_remote_fonts_and_low_contrast(tmp_path: Path):
    raw = json.loads(Path("themes/storyboard-tokens.json").read_text(encoding="utf-8"))
    raw["font_fallbacks"]["body"][0] = "https://fonts.example/private.woff2"
    raw["themes"]["midnight"]["text"] = raw["themes"]["midnight"]["bg"]
    invalid = tmp_path / "invalid-tokens.json"
    invalid.write_text(json.dumps(raw), encoding="utf-8")

    with pytest.raises(LayoutContractError, match="Font fallbacks|contrast"):
        load_layout_contract(invalid)


def test_brand_kit_is_local_contrast_checked_and_has_fallbacks():
    kit = load_brand_kit("themes/brand-kit.example.json")

    assert kit.name == "Northstar brand kit"
    assert kit.base_theme == "glacier"
    assert kit.display_font_fallbacks[-1] == "sans-serif"
    assert contrast_ratio(kit.colors.text, kit.colors.bg) >= 4.5


def test_overflow_preflight_offers_deterministic_recovery_actions():
    presentation = build_local_presentation("Shared layout contract", 3)
    presentation["slides"][0]["title"] = (
        "A deliberately long title that needs a deterministic layout correction now"
    )
    presentation["slides"][0]["content"] = " ".join(["evidence"] * 28)
    presentation["slides"][0]["layout"] = "right"

    report = analyze_overflow(presentation, load_layout_contract())

    assert report["status"] == "needs-fix"
    assert {finding["field"] for finding in report["findings"]} >= {"title", "content"}
    actions = {action["id"] for finding in report["findings"] for action in finding["actions"]}
    assert {"shorten", "use-focus"} <= actions
