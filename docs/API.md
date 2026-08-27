# Versioned local API

The current endpoints remain available at `/api/content` and
`/api/presentations` for compatibility. New integrations should use the
versioned aliases `/api/v1/content` and `/api/v1/presentations`; their request
and response shapes are described by `docs/schema/storyboard-v1.json`.

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
