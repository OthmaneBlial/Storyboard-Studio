# Golden example: recovery drill

![First slide rendered by LibreOffice 26.8.0.3](screenshot.png)

- Author input: [`examples/briefs/recovery-drill-decision.json`](../../examples/briefs/recovery-drill-decision.json)
- Compiled story: [`deck.story.json`](deck.story.json)
- Editable presentation: [`deck.pptx`](deck.pptx)
- Narrative Receipt: [`deck.receipt.json`](deck.receipt.json)
- Viewer result: LibreOffice 26.8.0.3 on macOS rendered all 6 slides; a
  structural check found 137 selectable native text shapes.

Regenerate from the repository root:

```bash
storyboard compile \
  --input examples/briefs/recovery-drill-decision.json \
  --output gallery/recovery-drill/deck.story.json
storyboard export \
  --input gallery/recovery-drill/deck.story.json \
  --output gallery/recovery-drill/deck.pptx \
  --bundle \
  --viewer-status "LibreOffice 26.8.0.3: rendered 6/6 slides on macOS; 137 native text shapes confirmed"
storyboard verify gallery/recovery-drill/deck.receipt.json
```
