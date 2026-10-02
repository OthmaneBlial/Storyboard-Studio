# Native story format v3

`.story.json` and `.storyboard` contain a typed JSON `Story`. Generate its schema
with `storyboard schema`. Unknown fields and versions are errors; imports never
silently drop unsupported content. The v3 format is currently a migration preview,
not the 1.0 compatibility promise.

A story owns audience, objective, owner, next action and metadata. Its presentation
owns title, subtitle, theme and ordered slides. Each slide has a stable ID, a purpose,
a narrative role, a layout, typed semantic blocks, explicit claims, evidence,
speaker notes and a transition. Claims are unique within a slide; evidence links
must resolve to those IDs. Author confirmation requires an owner, an excerpt and
checked date. URLs are never fetched by deterministic compilation or rendering.

Supported blocks: styled paragraphs/text, headings, cards, callouts, quotes,
metrics, local PNG/JPEG images, shapes/lines, native tables, bar/line/pie charts,
nested layout groups and explicitly positioned elements. Geometry uses points on
a 960×540 canvas. Stack, columns, grid and absolute placement are implemented;
hero/split/sidebar/overlay currently use bounded flow regions rather than an
independent constraint solver. Arbitrary font fidelity and complex-script shaping
are not yet supported: native layout measures the bundled OFL Carlito font.

Markdown briefs use one `# Deck title`, `## Slide conclusion` and optional
`### Card title`. Metadata before the first slide accepts `Audience:`, `Objective:`,
`Owner:`, `Next action:`, `Theme:`, `Author:` and `Synthetic: true`. `Notes:` on a
slide writes speaker notes. Other authored text is retained. This heading format
is a convenient input, not a lossless serialization of charts, styles or evidence.
Native JSON is the inspectable intermediate representation.

The prior typed v2 *decision brief* is accepted and recompiled from authored
fields. Prior v1 outlines, v2 story envelopes and old receipts are deliberately
rejected by the native path until an explicit semantic migration is implemented.
The working Python path and historical fixtures remain in place for comparison.

## Receipts and determinism

Rendering emits `.pptx`, `.story.json` and `.receipt.json`. Native ZIP timestamps
and part ordering are fixed, so identical story/theme/assets produce identical
PPTX bytes. Receipts use SHA-256 over exact artifact bytes, record the entire
resolved theme and replayable Doctor report, and refer only to sibling filenames.
Verification rejects escaped/symlinked artifacts, validates PPTX package integrity,
and replays diagnostics. The receipt is unsigned: a malicious party can replace
an entire bundle. It does not establish authorship or factual truth.

## Assets and security

Images must be relative regular files inside the input directory, with useful alt
text. Symlink escapes, absolute/parent paths, unsupported formats, oversized images
and invalid dimensions fail. Preview embeds images as data URIs. Evidence file
references are metadata only; the compiler never opens them. Hyperlinks require
HTTP(S), do not include credentials and are not followed during export.

PPTX validation reads a bounded archive, rejects traversal/duplicates/DTDs,
checks XML roots/namespaces, relationships and referenced media, and recovers
slide text. It is not a complete ECMA-376 schema validator or viewer certification.
