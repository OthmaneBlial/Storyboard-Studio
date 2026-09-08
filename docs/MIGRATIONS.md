# Schema and interchange migrations

The canonical models live in `storyboard_studio/schemas.py`; the top-level
`schemas.py` module is a compatibility shim for older imports. Generated JSON Schema and OpenAPI
files are release artifacts, not independent contracts to edit by hand.

## Presentation v1 to story v2

Presentation-v1 JSON is still accepted for rendering. Convert it into a
reviewable story explicitly:

```bash
storyboard migrate examples/product-brief.json --output output/product-brief.story.json
```

The migration uses `kind: freeform-outline`, `template: freeform`, and
`planner: imported`. It does not infer a decision brief, evidence status,
ownership, or factual certainty.

## Markdown interchange

Export a story, review it in Git, import it, or render it directly:

```bash
storyboard export --input output/product-brief.story.json --output output/product-brief.story.md
storyboard import output/product-brief.story.md --output output/restored.story.json
storyboard export --input output/product-brief.story.md --output output/restored.pptx
```

Storyboard metadata comments preserve theme, assets, brand kit, citations,
typed blocks, sources, notes, and the story envelope. Unknown constructs fail
with a line number. Removing the story envelope deliberately imports the file
as a freeform story; decision fields are never reconstructed from prose.

## Compatibility promise

- `storyboard-v1.json` and `/api/v1/*` receive only backward-compatible optional
  additions within v1.
- `story-v2.json` remains readable for the lifetime of the v0.x release line.
- A breaking field reinterpretation requires a new schema version, migration
  command or documented manual path, changelog entry, and at least one release
  warning where practical.
- Deprecated fields are never silently repurposed.
- Generated PPTX files remain user-owned and are never rewritten in place.

Run `make schema` after canonical model or route changes. CI regenerates the
JSON Schema and OpenAPI artifacts and fails when the checked-in contracts drift.

## Narrative Receipt v1 → v2

New exports use receipt schema `2`, canonicalization `sorted-json-utf8-v1`,
and diagnostics contract `1`. The outline hash covers the presentation object
as serialized in the companion story: UTF-8 JSON, sorted keys, compact
separators, preserved Unicode. Verification never inserts current model defaults
before hashing a historical object.

The verifier accepts legacy receipt schema `1` with scope
`legacy-artifact-integrity`. It checks the story and PPTX bytes and the original
outline hash; its `unverified_fields` explicitly includes historical diagnostics,
source coverage and provenance. Those reports have no versioned replay contract.
Legacy files are not rewritten. Regression fixtures live in
`tests/fixtures/receipts-v1/`.

For a new receipt, verification also recomputes Doctor results, evidence
coverage, sources, assets and author-edit metadata from the validated story.
Changes to that algorithm require a new diagnostics contract and an explicit
compatibility decision, rather than silently reinterpreting an old report.
Unknown receipt/canonicalization/diagnostics versions fail closed.

`renderer_version` and `viewer_status` are recorded declarations, never proof of
an Office check. Receipts are unsigned: changing a story and regenerating all
hashes cannot establish who authored it. A successful verification establishes
internal consistency, not factual truth or authenticity. Existing CLI `status`
and `checked` fields remain available; consumers should display `scope` and
`unverified_fields` as well.

To produce current diagnostics, export the original story with `--bundle` to a
new output location, then verify the resulting receipt. Keep the historical
bundle if its original byte identity matters. Invalid, missing, oversized or
non-object JSON returns an `invalid` report instead of an unhandled traceback.

## Unreleased dependency split after 0.2.0

The base install no longer includes Gemini or CairoSVG. Existing environments
keep their installed extras; new environments must request `[gemini]` or `[svg]`
from the same candidate when using those capabilities. SVG still requires native
Cairo. PNG/JPEG and native PowerPoint charts/tables remain in the base install.
Uvicorn's optional development/performance dependencies are no longer installed
by default; ordinary local HTTP serving remains supported.
