# Native delivery plan

The full accepted target is [REWRITE_SPEC.md](REWRITE_SPEC.md). This map does
not reduce that scope. The retired application is recoverable in Git history.
The native implementation owns all runtime paths.

| Existing behavior | Decision | Native owner / acceptance evidence |
| --- | --- | --- |
| `schemas.py`, versioned story/brief contracts | Redesign | `storyboard-core::model`; strict schema, validation, explicit version rejection |
| `story.py`, deterministic decision compilation | Rewrite | `storyboard-core::compiler`; author fields retained, options/evidence/action progression |
| `markdown.py`, editable Markdown interchange | Rewrite | Heading-based briefs, then lossless native story interchange |
| Semantic comparison, metric, timeline, quote blocks | Preserve | Typed block variants; rendered as editable objects |
| Doctor and claim-level evidence | Preserve and expand | Stable actionable diagnostics; never truth verification |
| `layout.py`, preflight, theme tokens | Redesign | Measured text and a resolved geometry tree shared by preview/PPTX |
| `renderer.py`, python-pptx | Rewrite | `storyboard-pptx`; direct OpenXML ZIP generation and package validation |
| Assets, charts, tables, notes, citations | Rewrite | Native objects and relationships, bounded local assets, tests |
| Receipts, story diffs | Preserve | Portable hash verification plus derived metadata validation |
| CLI and JSON tool integrations | Redesign | Native `storyboard`; validated library calls, machine output |
| FastAPI/browser studio, browser projects | Replace | Tauri commands, local project files/autosave, shared Rust core |
| Gemini/OpenAI-compatible draft providers | Rewrite | Explicit opt-in, bounded transfer, secrets never serialized |
| PyInstaller, pip/Docker installation | Remove after parity | Cargo + native release binaries + Tauri bundles |
| Legacy v1/v2 stories and receipts | Keep in Git history | Explicit version rejection; no silent default/drop of unsupported semantics |
| Existing gallery/benchmarks/viewer reports | Preserve as historical | New Rust gallery and measurements must have independent evidence |
| Template/contribution/research launch bureaucracy | Redesign | Simple scoped contribution guide, actual product evidence |
| Speculative plugins and future PDF exports | Defer | Clean module boundaries; PPTX stays the priority |

## Implementation sequence and completion gates

- [x] Typed Rust core, JSON/Markdown narrative compilation, strict validation.
- [x] Shared deterministic geometry, text measurement, overflow and image sizing.
- [x] Native editable PPTX: text, styling, shapes/lines, images, tables/charts,
      hyperlinks, notes, themes/layout/master, metadata and embedded assets.
- [x] Semantic PPTX validator: archive, XML, relationships, counts, recoverable text.
- [x] CLI: new/compile/render/build/doctor/inspect/verify/diff/preview/themes/examples/
      benchmark/serve; useful failures, JSON/Markdown diagnostics.
- [x] Versioned project schema, migration rules, custom themes and local brand kits.
- [x] Narrative/evidence coverage and tamper-resistant receipt verification.
- [x] Tauri: local home/recent projects, input/editor/map/doctor/evidence/themes/
      brand/export/settings/provider screens, autosave, shortcuts, drop/context menus.
- [x] Accurate preview: thumbnails/zoom/navigation/fit/fullscreen/grid.
- [x] Optional explicit AI providers, deterministic offline path independent.
- [x] 20 synthetic generated gallery examples, inputs/PPTX/story/receipt/diagnostics/previews.
- [ ] Current native screenshots, theme montage, clean README and responsive website.
- [ ] Real 10/25/50/100/250-slide measurements including startup/RSS/binary size.
- [ ] PowerPoint/LibreOffice compatibility; Keynote/Slides where feasible, bounded reports.
- [ ] Reproducible 30–60 second native product demo and capture workflow.
- [ ] Cross-platform CLI and desktop release preparation, downloadable binaries.
- [x] Remove all Python source, packaging, tests and tooling after native behavior
      coverage; no Python files in the final tree. Clean the root to the native
      workspace, product docs, examples and assets (owner clarification 2026-10-02).
- [ ] CONTRIBUTING/ARCHITECTURE/ROADMAP/SECURITY/CHANGELOG/templates reflect native state.

Each box needs current source and a passing check or observed artifact. Historical
Python tests and viewer reports cannot certify the Rust output. No registry publication
or new starter issues until justified; the owner requested the old issue/PR queue closed.
