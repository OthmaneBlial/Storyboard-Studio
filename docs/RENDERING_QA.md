# Rendering QA checklist

Run the structural suite on every change. Run the visual suite for a release
candidate or a renderer/layout change:

```bash
make export-sample
python3 scripts/render_slides.py docs/fixtures/product-brief.pptx --output rendered-slides --require
python3 scripts/generate_semantic_fixtures.py
python3 scripts/render_slides.py output/semantic-blocks/semantic-blocks-midnight.pptx --output rendered-semantic-midnight --require
python3 scripts/render_slides.py output/semantic-blocks/semantic-blocks-glacier.pptx --output rendered-semantic-glacier --require
make export-native-visuals
python3 scripts/render_slides.py output/native-visuals.pptx --output rendered-native-visuals --require
make export-evidence-fixture
python3 scripts/render_slides.py output/evidence-edge-cases.pptx --output rendered-evidence --require
```

The visual command prints the exact LibreOffice version, writes a PDF, and
creates PNGs when `pdftoppm` is installed. Review each page at 100% zoom and
compare it with the checked-in reference image. Do not commit generated
`rendered-slides/` output; attach it to the CI run when a mismatch needs
review.

The semantic fixture contains standard, comparison, decision, timeline,
metric, process, quote/evidence, and native table slides. The two generated
decks exercise the dark Midnight and light Glacier themes; their rendered PNGs
are uploaded by the manual visual CI job so every block can be reviewed for
clipping and viewer drift.

The native-visual fixture adds checksum-verified local CSV and SVG inputs. Its
rendered pages prove the bar, line, donut, and local-image paths in the reviewed
viewer; structural tests separately cover PNG and JPEG assets, image alt text,
native chart objects, table bounds, and provenance notes.

The evidence fixture adds Unicode, long bounded excerpts, an unresolved URL,
missing ownership, checked public/local references, full native notes, and an
author-approved citations appendix. The appendix must omit unresolved entries.

The manual `workflow_dispatch` visual job installs the runner's reviewed
LibreOffice package, prints its exact version, renders the fixture, and checks
the title slide against the approved reference with a mean pixel-error
tolerance of 12. The job is opt-in because office viewers are a release QA
dependency, not a requirement for contributors editing Python code.

The committed, versioned evidence for the latest local run lives in
[`docs/viewer-reports/`](viewer-reports/). Run `make validate-viewer-reports` in
CI to verify that every referenced fixture and contact sheet still matches its
recorded SHA-256; this check does not relabel an unrendered or missing viewer
run as PASS.

## Manual release checklist

- [ ] Title and body text have no clipping or overlap in all six themes.
- [ ] Accents and punctuation remain readable; missing fonts use a sensible
  fallback.
- [ ] Contrast is readable in dark and light themes.
- [ ] Every text box can be selected and edited.
- [ ] The browser preview and export contain the same reviewed copy.
- [ ] `storyboard preflight INPUT --fail-on-overflow` passes, or every visible
      finding is resolved with shorten, split, block review, or focus layout.
- [ ] The canvas is 16:9 at 75%, 100%, 125%, and 150% zoom; Outline mode remains
      usable at 320px without horizontal page overflow.
- [ ] Keyboard-only browser flow reaches controls in a logical order.
- [ ] The studio remains usable at 320px without horizontal overflow.
- [ ] Downloaded files open in PowerPoint and LibreOffice.

Record viewer name/version, OS, fixture, and result in
`docs/VIEWER_MATRIX.md` for each release candidate.
