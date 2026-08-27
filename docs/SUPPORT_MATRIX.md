# Support and compatibility baseline

This document defines the baseline tested by each Storyboard Studio release.

| Surface | Baseline | Policy |
| --- | --- | --- |
| Python | 3.10–3.14 | Supported while the upstream runtime receives security updates; CI covers the declared range where runners are available. |
| OS | Linux, macOS, Windows | The local HTTP server and CLI are the supported path. Packaging-specific issues should include OS and architecture. |
| Browser | Current Chrome, Firefox, Safari, and Edge | The studio uses standards-based HTML/CSS/JavaScript; the release checklist covers keyboard and narrow viewport behavior. |
| Viewer | Microsoft PowerPoint desktop and LibreOffice Impress | Native text and shapes are the compatibility contract. Viewer version and platform belong in bug reports. |
| Output | 16:9 `.pptx`, 3–10 content slides plus title slide | Fonts use fallbacks; unsupported Office features are documented instead of silently approximated. |
| Interchange | Story/presentation JSON and strict `.md` / `.markdown` | Sources, notes, typed blocks, assets, and review metadata round-trip deterministically. Unknown Markdown constructs fail with a line number. |
| Source material | Local `.md` and `.txt` in the browser | The full file stays in the tab; only selected excerpts and line boundaries enter the story. DOCX and PDF are explicitly unsupported. |

## Deprecation policy

Public request fields and the validated outline schema are versioned contracts.
Breaking changes require a changelog entry, migration notes, and one release
with a deprecation warning where practical. Security fixes may narrow support
immediately. Old generated files remain user-owned; Storyboard Studio never
rewrites them.

The exact migration commands and version promises are maintained in
[`MIGRATIONS.md`](MIGRATIONS.md). Generated contracts live under
[`schema/`](schema/), including the versioned OpenAPI document and validated
examples.
