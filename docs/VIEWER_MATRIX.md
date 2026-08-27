# Release-candidate viewer matrix

The matrix is deliberately explicit: a structural ZIP check is not evidence
that a viewer rendered the deck correctly.

| Viewer | Platform | Fixture | Result | Checked |
| --- | --- | --- | --- | --- |
| Microsoft PowerPoint desktop (Microsoft 365) | macOS 26.0 (Apple Silicon) | `docs/fixtures/product-brief.pptx` | PASS — PowerPoint opened the 4-slide deck through AppleScript smoke check | 2026-08-26 |
| LibreOffice Impress 26.8.0.3 | macOS 26.0 (Apple Silicon) | `docs/fixtures/product-brief.pptx` | PASS — rendered 4-page PDF/PNG output; title slide inspected and mean visual error was 6.22 (<12 tolerance) | 2026-08-26 |
| LibreOffice Impress 26.8.0.3 | macOS 26.0 (Apple Silicon) | generated `semantic-blocks-midnight.pptx` | PASS — all 8 semantic blocks rendered to a 9-page PDF/PNG set; contact sheet inspected with no clipping or off-slide shapes | 2026-08-27 |
| LibreOffice Impress 26.8.0.3 | macOS 26.0 (Apple Silicon) | generated `semantic-blocks-glacier.pptx` | PASS — all 8 semantic blocks rendered to a 9-page PDF/PNG set; contact sheet inspected with no clipping or off-slide shapes | 2026-08-27 |
| LibreOffice Impress 26.8.0.3 | macOS 26.0 (Apple Silicon) | `assets/demo/native-visuals.json` | PASS — native bar, line, and donut charts plus the sanitized local SVG rendered to a 5-page PDF/PNG set; contact sheet inspected with no clipping | 2026-08-27 |
| Apple Keynote import | — | canonical fixture set | UNVERIFIED — no versioned manual import/edit report; no parity claim | — |
| Google Slides import | — | canonical fixture set | UNVERIFIED — requires an authorized upload to a third party; no parity claim | — |

This repository cannot claim a viewer result from `python-pptx` alone. The
checks above used the local release-candidate fixture; rerun them after
renderer or layout changes. Known discrepancies belong in
`docs/EXPORT_COMPATIBILITY.md`.
