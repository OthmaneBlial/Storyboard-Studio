# Golden example: onboarding pilot

![Historical first slide rendered by LibreOffice 26.8.0.3](screenshot.png)

- Author input: [`examples/briefs/onboarding-decision.json`](../../examples/briefs/onboarding-decision.json)
- Compiled story: [`deck.story.json`](deck.story.json)
- Editable presentation: [`deck.pptx`](deck.pptx)
- Narrative Receipt: [`deck.receipt.json`](deck.receipt.json)
- Viewer result for the regenerated deck: **not run**. The screenshot above
  belongs to the historical August fixture, not this regenerated PowerPoint.
  Current Office rendering and native-edit checks remain a release gate.
- Receipt v2 verifies the current files and recomputes derived review metadata;
  it does not authenticate an author or certify factual truth.

Regenerate from the repository root:

```bash
storyboard compile \
  --input examples/briefs/onboarding-decision.json \
  --output gallery/onboarding-pilot/deck.story.json
storyboard export \
  --input gallery/onboarding-pilot/deck.story.json \
  --output gallery/onboarding-pilot/deck.pptx \
  --bundle
storyboard verify gallery/onboarding-pilot/deck.receipt.json
```
