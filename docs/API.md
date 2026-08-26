# Versioned local API

The current endpoints remain available at `/api/content` and
`/api/presentations` for compatibility. New integrations should use the
versioned aliases `/api/v1/content` and `/api/v1/presentations`; their request
and response shapes are described by `docs/schema/storyboard-v1.json`.

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

Breaking changes use a new `/api/v2` namespace and a new schema `$id`.
Additive fields remain optional in v1. The server never stores request bodies;
only the generated PPTX is retained until its 24-hour expiry.
