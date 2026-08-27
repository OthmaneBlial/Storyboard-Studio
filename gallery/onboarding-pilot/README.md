# Golden example: onboarding pilot

![First slide rendered by LibreOffice 26.8.0.3](screenshot.png)

- Author input: [`examples/briefs/onboarding-decision.json`](../../examples/briefs/onboarding-decision.json)
- Compiled story: [`deck.story.json`](deck.story.json)
- Editable presentation: [`deck.pptx`](deck.pptx)
- Narrative Receipt: [`deck.receipt.json`](deck.receipt.json)
- Viewer result: LibreOffice 26.8.0.3 on macOS rendered all 6 slides; a
  structural check found 137 selectable native text shapes. The app-only
  [workflow recording](../../docs/assets/storyboard-demo-app-only.mp4) also edits this
  deck's title live in LibreOffice Impress.

Regenerate from the repository root:

```bash
storyboard compile \
  --input examples/briefs/onboarding-decision.json \
  --output gallery/onboarding-pilot/deck.story.json
storyboard export \
  --input gallery/onboarding-pilot/deck.story.json \
  --output gallery/onboarding-pilot/deck.pptx \
  --bundle \
  --viewer-status "LibreOffice 26.8.0.3: rendered 6/6 slides on macOS; 137 native text shapes confirmed"
storyboard verify gallery/onboarding-pilot/deck.receipt.json
```
