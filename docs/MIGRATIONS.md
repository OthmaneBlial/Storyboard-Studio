# Schema and interchange migrations

The canonical models live in `schemas.py`. Generated JSON Schema and OpenAPI
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
