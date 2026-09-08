import shutil
from pathlib import Path

import pytest

from scripts.validate_site import validate_site


def test_public_site_is_portable_and_search_ready():
    report = validate_site(Path("site"))

    assert report["pages"] == 2
    assert report["json_ld_documents"] == 1
    assert report["sitemap_urls"] == 2
    assert report["local_links"] >= 12


def test_site_validator_rejects_a_missing_local_asset(tmp_path: Path):
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.html").write_text('<img src="missing.png">', encoding="utf-8")

    with pytest.raises(ValueError, match="Missing required site files"):
        validate_site(site)


def test_site_validator_requires_current_ai_proof_assets(tmp_path: Path):
    site = tmp_path / "site"
    shutil.copytree("site", site)
    (site / "assets" / "storyboard-demo-ai.mp4").unlink()

    with pytest.raises(ValueError, match="storyboard-demo-ai.mp4"):
        validate_site(site)


def test_social_preview_source_and_public_copy_match():
    source = Path("docs/assets/social-preview.png").read_bytes()
    public_copy = Path("site/assets/social-preview.png").read_bytes()
    assert source == public_copy
