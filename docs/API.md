# Versioned local API

The current endpoints remain available at `/api/content` and
`/api/presentations` for compatibility. New integrations should use the
versioned aliases `/api/v1/content` and `/api/v1/presentations`; their request
and response shapes are described by `docs/schema/storyboard-v1.json`.

`GET /api/v1/providers` returns the provider catalogue before generation:
model configuration, supported state, network boundary, structured-output
capability, timeout, cost and retention disclosures, maintainer, conformance
suite, exact transferred fields, and excluded private fields.

`POST /api/v1/content` accepts optional `provider: local | gemini |
openai-compatible`. `local` is the recommended explicit value. The legacy
`use_ai` boolean remains compatible only when `provider` is omitted. Responses
include a `provider` run record with `selected`, `used`, models, network status,
and a stable fallback reason. Unknown file, asset, or evidence request fields
fail schema validation and are never forwarded.

`POST /api/v1/doctor` accepts the same validated presentation payload and
returns deterministic, explainable findings about narrative structure,
evidence coverage, copy density, and the final action. It never calls an AI
provider and does not claim to verify factual truth.

`POST /api/v1/stories/decision-brief` accepts the structured schema v2 decision
fields and returns a deterministic local story plus its presentation payload.
`POST /api/v1/stories/doctor` diagnoses that versioned story while preserving
accepted, ignored-with-reason, and resolved dispositions. `POST
/api/v1/bundles` returns a temporary ZIP download containing `deck.pptx`,
`deck.story.json`, and `deck.receipt.json`.

```bash
curl -s http://127.0.0.1:8000/api/v1/content \
  -H 'content-type: application/json' \
  -d '{"topic":"A private decision brief","slide_count":3,"use_ai":false}'
```

```python
import requests

outline = requests.post(
    "http://127.0.0.1:8000/api/v1/content",
    json={"topic": "A private decision brief", "slide_count": 3, "use_ai": False},
    timeout=30,
).json()
deck = requests.post(
    "http://127.0.0.1:8000/api/v1/presentations",
    json={"presentation": outline["presentation"]},
    timeout=30,
).json()
print(deck["download_url"])
```

```bash
curl -s http://127.0.0.1:8000/api/v1/doctor \
  -H 'content-type: application/json' \
  --data-binary @examples/product-brief.json
```

Breaking changes use a new `/api/v2` namespace and a new schema `$id`.
Additive fields remain optional in v1. The server never stores request bodies;
only generated PPTX or ZIP downloads are retained until their 24-hour expiry.

New presentation payloads may use the discriminated `content_block` contract
for standard, comparison, decision, timeline, metric, process, quote/evidence,
or table slides. A slide's `block` value must match `content_block.type`.
Legacy three-bullet payloads remain accepted through the documented v1
compatibility adapter.

Presentation payloads can also include up to 12 strict local `assets`. Chart
blocks reference checksum-verified CSV/JSON data; image blocks reference local
PNG, JPEG, or sanitized SVG files. Paths are resolved relative to the input
file for CLI export and relative to the server working directory for browser/API
export. Remote, absolute, parent-traversal, missing, mismatched, unreadable, or
oversized assets are rejected before a PPTX is written.

Each slide source supports `label`, `evidence`, `owner`, public HTTP(S) `url`,
relative `local_reference`, `checked_date`, optional `license`, explicit
`review_status`, and local `claim_ids`. Private/malicious URLs and path
traversal fail validation. `author-checked` requires owner, date, and a locator;
URL presence alone remains unresolved.

`POST /api/v1/evidence/coverage` returns claim and slide coverage without
network access or factual-verification claims. Set `citations_appendix: true`
on a presentation to append native citation pages containing author-checked
entries only.

`GET /api/v1/layout-contract` exposes the validated local v2 canvas, geometry,
typography, font fallback, overflow, and theme tokens used by both the HTML
preview and PowerPoint renderer. `POST /api/v1/layout/preflight` accepts a
validated presentation payload and returns `ready` or `needs-fix`, precise
slide/field paths, character budgets, and deterministic recovery actions. The
browser checks this endpoint before export and never silently clips flagged
copy.

An optional `brand_kit` presentation field accepts the constrained schema v1
contract documented in `docs/LAYOUT_CONTRACT.md`. It contains only local color
and font-family values; URLs, weak contrast, missing generic fallbacks, and
unknown fields fail request validation.

The generated [`schema/openapi-v1.json`](schema/openapi-v1.json) document comes
from these live FastAPI routes and the same Pydantic models as the JSON Schema.
It embeds validated no-key content, guided-decision, and presentation-export
request examples. Regenerate all public contracts with `make schema`; use
`make schema-check` to detect drift. Migration behavior and the additive-change
promise are specified in [`MIGRATIONS.md`](MIGRATIONS.md).
