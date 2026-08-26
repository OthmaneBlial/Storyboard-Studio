# Public schema

`storyboard-v1.json` is generated from the strict Pydantic request models. It
describes the body accepted by `POST /api/presentations` and is intended for
templates, CI jobs, and integrations that want to validate before contacting a
local server.

Regenerate and verify it with:

```bash
make schema
```

The small input example in `examples/fixtures/edge-cases.json` demonstrates the
shape without requiring an API key.
