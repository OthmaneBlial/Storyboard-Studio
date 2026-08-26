# Release-candidate viewer matrix

The matrix is deliberately explicit: a structural ZIP check is not evidence
that a viewer rendered the deck correctly.

| Viewer | Platform | Fixture | Result | Checked |
| --- | --- | --- | --- | --- |
| Microsoft PowerPoint desktop (Microsoft 365) | macOS 26.0 (Apple Silicon) | `docs/fixtures/product-brief.pptx` | PASS — PowerPoint opened the 4-slide deck through AppleScript smoke check | 2026-08-26 |
| LibreOffice Impress 26.8.0.3 | macOS 26.0 (Apple Silicon) | `docs/fixtures/product-brief.pptx` | PASS — rendered 4-page PDF/PNG output; title slide inspected and mean visual error was 6.22 (<12 tolerance) | 2026-08-26 |

This repository cannot claim a viewer result from `python-pptx` alone. The
checks above used the local release-candidate fixture; rerun them after
renderer or layout changes. Known discrepancies belong in
`docs/EXPORT_COMPATIBILITY.md`.
