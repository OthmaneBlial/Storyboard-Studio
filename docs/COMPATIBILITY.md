# Native viewer observations — 2026-10-02

These are observations of actual 0.3 native artifacts, not universal certification.

| Viewer | Artifact / scope | Observed result |
| --- | --- | --- |
| LibreOffice 26.8.0.3, macOS 26.6 arm64 | All 20 `gallery/native` decks, 7–9 slides each | Independent PDF rendering completed; authored visible text token checks passed on every slide. Each folder records viewer version, deck SHA-256 and per-slide checks. |
| Keynote 13.1, macOS 26.6 | `gallery/native/startup-pitch/deck.pptx`, 9 slides | Imported without an observed repair warning; navigator shows all nine slides. First slide title selected as a native editable Textbox, Carlito Bold 40pt shown in inspector; text and line objects exposed separately. Screenshot: `docs/screenshots/native/keynote.png`. |
| PowerPoint 16.113.3, macOS 26.6 | Same startup deck selected in native local picker | Open stayed disabled in this automation session. No document render or edit was observed; PowerPoint compatibility remains unverified. |
| Google Slides | — | Not uploaded or exercised in this run. |

Startup deck SHA-256:
`b8d9fdfc8233bfa1707f3dbe37918e0d574009a08a73760c46dcafc634f3b26e`.
No changes were saved over the generated gallery artifact during viewer checks.

LibreOffice token checks exclude native chart labels and image content; they do
not prove editability or exact geometry. Keynote's selected textbox proves that
object is editable, not every chart or table in every deck. OpenXML semantic tests
cover images, tables, charts/workbooks, links, notes and relationships separately.

Reproduce independent gallery checks with `make office` (LibreOffice and Poppler
required). For a new viewer, open a current deck, record version/hash, inspect the
first and densest slides, edit text/table/chart data on a disposable copy, inspect
notes/links/images, save and reopen it, then record warnings and differences.

## Desktop observations

Production Apple Silicon bundle: compilation, Story Map, slide properties, Doctor,
12 themes, native local brand import, provider request to a loopback fixture,
export plus receipt verification, palette filtering/Enter/arrow activation,
light appearance, fullscreen preview, grid slide selection and recent-project
reopening were exercised. The exact approved provider input reached the local
fixture; no external provider was called. A saved custom theme and logo survived
closing/reopening the app. These observations do not certify Windows/Linux/Intel
builds or an external provider account.
