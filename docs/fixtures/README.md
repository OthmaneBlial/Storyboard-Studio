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
python3 generate_pptx.py --input examples/product-brief.json --output docs/fixtures/product-brief.pptx
```
