"""Render a lightweight, browser-free title-slide poster from a JSON brief.

This is a shareable preview asset, not a substitute for opening the generated
PowerPoint in a viewer.  Keeping it deterministic makes the public showcase
reproducible without launching Office applications.
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

import cairosvg

WIDTH = 1865
HEIGHT = 1050


def _lines(value: str, limit: int) -> list[str]:
    words = value.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > limit:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def render(input_path: Path, output_path: Path, svg_path: Path | None = None) -> None:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    title = str(data.get("title", "Untitled presentation")).strip()
    subtitle = str(data.get("subtitle", "")).strip()
    title_lines = _lines(title, 21)
    subtitle_lines = _lines(subtitle, 43)
    title_svg = "".join(
        f'<tspan x="136" dy="{0 if index == 0 else 106}">{html.escape(line)}</tspan>'
        for index, line in enumerate(title_lines[:3])
    )
    subtitle_svg = "".join(
        f'<tspan x="140" dy="{0 if index == 0 else 48}">{html.escape(line)}</tspan>'
        for index, line in enumerate(subtitle_lines[:3])
    )
    font_family = "Arial, Helvetica, sans-serif"
    svg = "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
            f'viewBox="0 0 {WIDTH} {HEIGHT}">',
            f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#F1F5EE"/>',
            '<rect x="1365" width="500" height="1050" fill="#E0EADD"/>',
            '<rect x="76" y="90" width="14" height="827" rx="2" fill="#438360"/>',
            f'<text x="140" y="139" fill="#438360" font-family="{font_family}" '
            'font-size="22" font-weight="700" letter-spacing="1">STORYBOARD STUDIO</text>',
            f'<text x="136" y="301" fill="#1D3829" font-family="{font_family}" '
            f'font-size="94" font-weight="700" letter-spacing="-2">{title_svg}</text>',
            f'<text x="140" y="640" fill="#577060" font-family="{font_family}" '
            f'font-size="39" font-weight="400">{subtitle_svg}</text>',
            '<rect x="1449" y="140" width="337" height="22" fill="#438360"/>',
            f'<text x="1449" y="229" fill="#1D3829" font-family="{font_family}" '
            'font-size="32" font-weight="700">',
            '<tspan x="1449" dy="0">A concise, editable</tspan><tspan x="1449" dy="38">deck</tspan>',
            "</text>",
            f'<text x="1449" y="341" fill="#577060" font-family="{font_family}" '
            'font-size="30" font-weight="400">',
            '<tspan x="1449" dy="0">Prepared for a clear</tspan>',
            '<tspan x="1449" dy="38">conversation, not a</tspan>',
            '<tspan x="1449" dy="38">wall of slides.</tspan>',
            "</text>",
            '<rect x="1365" y="658" width="500" height="392" fill="#438360"/>',
            f'<text x="1449" y="773" fill="#F1F5EE" font-family="{font_family}" '
            'font-size="34" font-weight="700">',
            '<tspan x="1449" dy="0">NATIVE</tspan><tspan x="1449" dy="43">POWERPOINT</tspan>',
            "</text>",
            f'<text x="1449" y="931" fill="#D0DFC9" font-family="{font_family}" '
            'font-size="18" font-weight="700" letter-spacing="2">'
            "PRIVATE AI · HUMAN SIGN-OFF</text>",
            "</svg>",
        ]
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cairosvg.svg2png(
        bytestring=svg.encode("utf-8"),
        write_to=str(output_path),
        output_width=WIDTH,
        output_height=HEIGHT,
    )
    if svg_path:
        svg_path.parent.mkdir(parents=True, exist_ok=True)
        svg_path.write_text(svg, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--svg", type=Path)
    args = parser.parse_args()
    render(args.input, args.output, args.svg)
    print(f"Rendered poster {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
