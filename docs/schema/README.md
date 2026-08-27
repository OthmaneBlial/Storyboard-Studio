# Public schema

`storyboard-v1.json` is generated from the strict Pydantic export models. It
describes the body accepted by `POST /api/presentations` and is intended for
templates, CI jobs, and integrations that want to validate before contacting a
local server.

Regenerate and verify it with:

```bash
make schema
```

`story-v2.json` is the versioned reviewable story document used by guided
decision briefs, Doctor dispositions, Narrative Receipts, migration, and diff.
Both schemas are also packaged in the installed wheel under
`storyboard_studio/data/`.

The small input example in `examples/fixtures/edge-cases.json` demonstrates the
shape without requiring an API key.

`examples/fixtures/semantic-blocks.json` exercises the typed standard,
comparison, decision, timeline, metric, process, quote/evidence, and table
contracts. Legacy three-bullet slides remain valid through an explicit adapter;
new authored stories should use `content_block`.
