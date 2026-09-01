"""Validate the portable Storyboard Studio showcase and its SEO contract."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit

PAGES = {
    "index.html": "https://othmaneblial.github.io/Storyboard-Studio/",
    "docs.html": "https://othmaneblial.github.io/Storyboard-Studio/docs.html",
}
REQUIRED_FILES = (
    "app.js",
    "favicon.svg",
    "llms.txt",
    "robots.txt",
    "site.webmanifest",
    "sitemap.xml",
    "styles.css",
    "assets/social-preview.png",
    "assets/storyboard-sample.png",
)
ATTRIBUTE_RE = re.compile(r"(?:href|src)=\"([^\"]+)\"")
JSON_LD_RE = re.compile(r'<script\s+type="application/ld\+json">\s*(.*?)\s*</script>', re.DOTALL)
TITLE_RE = re.compile(r"<title>([^<]+)</title>")
DESCRIPTION_RE = re.compile(r'<meta name="description" content="([^"]+)">')


def _local_target(site_dir: Path, page: Path, value: str) -> Path | None:
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None
    return (page.parent / parsed.path).resolve()


def validate_site(site_dir: Path) -> dict[str, int]:
    site_dir = site_dir.resolve()
    missing = [name for name in REQUIRED_FILES if not (site_dir / name).is_file()]
    if missing:
        raise ValueError("Missing required site files: " + ", ".join(missing))

    local_links = 0
    json_ld_documents = 0
    for filename, canonical in PAGES.items():
        page = site_dir / filename
        html = page.read_text(encoding="utf-8")
        required_fragments = (
            '<meta name="description"',
            '<meta name="robots"',
            f'<link rel="canonical" href="{canonical}">',
            '<meta property="og:title"',
            '<meta property="og:description"',
            '<meta property="og:image"',
            '<meta name="twitter:card" content="summary_large_image">',
        )
        absent = [fragment for fragment in required_fragments if fragment not in html]
        if absent:
            raise ValueError(f"{filename} is missing metadata: {', '.join(absent)}")
        title_match = TITLE_RE.search(html)
        description_match = DESCRIPTION_RE.search(html)
        if title_match is None or not 30 <= len(title_match.group(1)) <= 60:
            raise ValueError(f"{filename} title must contain 30 to 60 characters")
        if description_match is None or not 120 <= len(description_match.group(1)) <= 160:
            raise ValueError(f"{filename} description must contain 120 to 160 characters")
        for value in ATTRIBUTE_RE.findall(html):
            target = _local_target(site_dir, page, value)
            if target is None:
                continue
            local_links += 1
            if site_dir not in target.parents and target != site_dir:
                raise ValueError(f"{filename} links outside the portable site: {value}")
            if not target.is_file():
                raise ValueError(f"{filename} has a missing local target: {value}")

        for payload in JSON_LD_RE.findall(html):
            document = json.loads(payload)
            if document.get("@context") != "https://schema.org":
                raise ValueError(f"{filename} JSON-LD does not use Schema.org")
            json_ld_documents += 1

    index_html = (site_dir / "index.html").read_text(encoding="utf-8")
    if '"@type": "SoftwareApplication"' not in index_html:
        raise ValueError("index.html is missing SoftwareApplication structured data")
    if '"@type": "VideoObject"' not in index_html:
        raise ValueError("index.html is missing VideoObject structured data for the real demo")

    manifest = json.loads((site_dir / "site.webmanifest").read_text(encoding="utf-8"))
    if manifest.get("start_url") != "./" or not manifest.get("icons"):
        raise ValueError("site.webmanifest must remain subpath-portable and include an icon")

    sitemap = ET.parse(site_dir / "sitemap.xml")
    locations = {
        node.text
        for node in sitemap.findall(
            "{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc"
        )
    }
    if locations != set(PAGES.values()):
        raise ValueError("sitemap.xml does not match the public page contract")

    robots = (site_dir / "robots.txt").read_text(encoding="utf-8")
    if "Sitemap: https://othmaneblial.github.io/Storyboard-Studio/sitemap.xml" not in robots:
        raise ValueError("robots.txt does not advertise the canonical sitemap")

    return {
        "pages": len(PAGES),
        "local_links": local_links,
        "json_ld_documents": json_ld_documents,
        "sitemap_urls": len(locations),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("site_dir", nargs="?", type=Path, default=Path("site"))
    args = parser.parse_args()
    report = validate_site(args.site_dir)
    print(f"Site valid: {json.dumps(report, sort_keys=True)}")


if __name__ == "__main__":
    main()
