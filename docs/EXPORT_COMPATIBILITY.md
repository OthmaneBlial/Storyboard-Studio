# Export compatibility contract

Storyboard Studio exports a 16:9 Office Open XML presentation (`.pptx`) with
one title slide and 3–10 content slides. The renderer creates native text boxes
and shapes with `python-pptx`; it does not embed screenshots of the preview.

## Supported baseline

- **Viewers:** Microsoft PowerPoint desktop and LibreOffice Impress. Include
  viewer name/version and OS in compatibility reports.
- **Canvas:** 13.333 × 7.5 inches (16:9 widescreen).
- **Fonts:** `Aptos Display` for headings and `Aptos` for body text, with the
  viewer’s normal font substitution when those fonts are unavailable. The
  layout contract avoids depending on a particular font’s exact metrics.
- **Language direction:** left-to-right Latin text, including Unicode accents
  and punctuation. Right-to-left scripts are not yet a supported layout
  guarantee.
- **Themes:** midnight, glacier, ember, forest, royal, and sakura. Each uses
  a documented background, surface, text, muted, and accent color token.
- **Safe area:** content stays inside a 0.55-inch outer margin and the renderer
  uses bounded text boxes; viewers may substitute fonts, so concise copy is
  preferred over relying on exact line breaks.

## What stays editable

| Element | Contract |
| --- | --- |
| Title, subtitle, semantic block fields, footer | Selectable PowerPoint text with a normal text cursor. |
| Cards, rules, panels, accent bars | Native PowerPoint shapes that can be moved, recolored, or deleted. |
| Tables | Native PowerPoint tables with independently editable cells, bounded to 2–4 columns and 1–5 body rows. |
| Slide order and theme | Encoded in the generated file; changing them after export is a normal viewer operation. |
| Shared layout / local brand kit | Validated runtime geometry, contrast-checked RGB colors, and local font-family fallbacks; no remote font or template fetch. |
| Images | Checksum-verified local PNG/JPEG files and sanitized local SVG files are independently movable pictures. SVG is rasterized locally; attribution, license, checksum, and alt text remain in provenance. |
| Charts | Native editable bar, line, and donut charts from bounded local CSV/JSON data, with visible source notes. |
| Evidence and citations | Complete source metadata remains in native notes; optional appendix pages contain author-checked entries as editable text/shapes. |

## Preview and viewer parity limits

Parity means preserving reviewed meaning and bounded major geometry. It does
not mean that every browser editing control or every viewer rasterizes the same
pixels.

| Surface / viewer | Guaranteed boundary | Explicit limit | Release gate |
| --- | --- | --- | --- |
| Browser Canvas | Exact presentation title/subtitle, slide order, slide titles/summaries, typed block role and fields, source copy, theme/brand tokens, 16:9 canvas, and the shared heading/summary/content/visual frames. Major frame edges track the token contract within 1% of canvas width/height. | The canvas shows editable block controls and a semantic visual frame, not a pixel preview of native Office tables, charts, images, notes, or viewer-specific line wrapping. | Five Chromium flows, including 320px Outline mode, zoom, overflow recovery, copy parity, and export. |
| Microsoft PowerPoint desktop | Target OOXML viewer: native text, shapes, tables, charts, pictures, order, notes, alt text, colors, and positions are expected to remain editable. Renderer coordinates match token inches to the OOXML EMU. | Installed fonts and Office version can change line breaks, chart defaults, and antialiasing. Animation, transitions, macros, arbitrary templates, and media are not emitted. | Manual release-candidate open/edit check recorded in `VIEWER_MATRIX.md`. |
| LibreOffice Impress | Supported secondary viewer: deck/page count, selectable text, native object structure, source notes, and on-canvas bounds must survive import/render. | Font metrics, chart labels/legend placement, SVG rasterization, rounded corners, and small spacing can differ from PowerPoint. Pixel comparison is valid only against a baseline rendered by the same viewer/version; current reviewed title tolerance is mean absolute RGB error ≤12. | Manual/CI PDF+PNG render of product, semantic-block, and native-visual fixtures with exact viewer version recorded. |
| Apple Keynote import | No current parity guarantee; an imported `.pptx` should be treated as an interoperability experiment. | Native chart/table styling, fonts, notes, alt text, grouping, and spacing may change. A successful file open is not a PASS. | Not a release gate until a versioned manual fixture report exists. Current status: unverified. |
| Google Slides import | No current parity guarantee; upload/conversion leaves the local-first execution boundary. | Upload shares the deck with Google; fonts, charts, notes, alt text, image handling, and geometry may be converted or reflowed. Storyboard Studio does not automate or silently perform this upload. | Not a release gate until an authorized, versioned manual fixture report exists. Current status: unverified. |

Cross-surface acceptance is therefore structural: exact reviewed copy and
ordering, exact semantic block identity, no off-canvas objects, and major frame
geometry within the stated tolerance. Cross-viewer pixel identity is not part
of the contract.

## Known limits

The current product intentionally has no arbitrary PowerPoint template import,
animations, transitions, embedded media, generative image provider, or right-to-left layout
guarantee. Text is validated and bounded by the public schema; clients should
revise very long copy before export rather than expect silent overflow repair.
Unsupported or malformed input is rejected by the API instead of being written
to a partially valid deck.

## Reporting a mismatch

Use the fixture in `docs/fixtures/product-brief.pptx`, a synthetic payload from
`examples/fixtures/edge-cases.json`, or the complete typed-block fixture in
`examples/fixtures/semantic-blocks.json`. Attach a screenshot with private
text removed, the viewer version, OS, theme, layout, and the commit that
generated the file.
