# Reference fixture

`product-brief.pptx` is generated from `examples/product-brief.json` with the
same renderer used by the application. It is intentionally small and contains
Unicode-safe, editable native text and shapes.

The public visual reference is [`../assets/storyboard-sample.png`](../assets/storyboard-sample.png),
which shows the title-slide treatment. The fixture is suitable for opening in
PowerPoint or LibreOffice and for structural regression tests. Viewer-specific
differences belong in `docs/EXPORT_COMPATIBILITY.md`.

Regenerate it with:

```bash
storyboard export --input examples/product-brief.json --output docs/fixtures/product-brief.pptx
```

## Private AI preview

The showcase's current AI example is [`product-brief-ai.pptx`](product-brief-ai.pptx),
generated from [`examples/product-brief-ai.json`](../../examples/product-brief-ai.json).
It is paired with the browser-free poster preview at
[`../assets/storyboard-ai-sample.png`](../assets/storyboard-ai-sample.png).
Regenerate both assets without launching an Office application:

```bash
storyboard export --input examples/product-brief-ai.json --output docs/fixtures/product-brief-ai.pptx
.venv/bin/python scripts/render_poster.py examples/product-brief-ai.json docs/assets/storyboard-ai-sample.png
cp docs/assets/storyboard-ai-sample.png site/assets/storyboard-ai-sample.png
```

The poster is a deterministic marketing preview. Viewer compatibility and
native editability still require the explicit checks described in
[`../EXPORT_COMPATIBILITY.md`](../EXPORT_COMPATIBILITY.md).
