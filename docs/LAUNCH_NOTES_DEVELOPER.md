# Launch note for developers

Storyboard Studio exposes a strict Pydantic contract, a named `storyboard`
CLI, versioned `/api/v1` aliases, and deterministic Markdown interchange. The
renderer emits native `python-pptx` text and shapes and has an opt-in
LibreOffice visual QA path.

```bash
make setup
make test
make smoke
make markdown-roundtrip
```

Useful contribution surfaces are templates, accessibility, renderer fixtures,
viewer compatibility reports, and provider adapters that preserve the local
fallback. See [`CONTRIBUTING.md`](../CONTRIBUTING.md), the
[template contract](TEMPLATE_CONTRACT.md), and the [bounded queue](GOOD_FIRST_ISSUES.md).
