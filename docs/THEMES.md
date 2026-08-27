# Themes and editorial blocks

![Six Storyboard Studio themes](assets/theme-gallery.svg)

The six themes share the validated runtime contract in
`themes/storyboard-tokens.json`: a 0.55-inch outer margin, bounded text boxes, a
16:9 canvas, explicit overflow budgets, and contrast-aware
text/muted/accent tokens. The browser and renderer consume the same values. The
renderer uses `Aptos Display`/`Aptos` when available and retains local generic
fallbacks without changing the canvas.

| Theme | Intended use | Contrast rule | Supported blocks |
| --- | --- | --- | --- |
| Midnight | Decisive briefings and product narratives | Light text on deep navy; ochre accent | Standard, comparison, decision, timeline, metric |
| Glacier | Calm analysis and field notes | Navy text on pale blue-gray; teal accent | Standard, comparison, decision, timeline, metric |
| Ember | Urgent change and creative studies | Warm light text on dark brown; orange accent | Standard, comparison, decision, timeline, metric |
| Forest | Practical plans and humane operations | Deep green text on pale green; green accent | Standard, comparison, decision, timeline, metric |
| Royal | Premium strategy and archival material | Cream text on near-black; gold accent | Standard, comparison, decision, timeline, metric |
| Sakura | Personal, editorial, reflective work | Plum text on soft pink; rose accent | Standard, comparison, decision, timeline, metric |

Editorial blocks are native PowerPoint shapes, not images:

- **Comparison** adds a before/after pair.
- **Decision** adds an explicit directional chevron.
- **Timeline** adds three sequence markers.
- **Metric** adds a large signal callout.
- **Standard** keeps the neutral key-frame treatment.

Every block provides an accessible plain-text equivalent.
If a viewer substitutes fonts or has accessibility settings enabled, content
remains selectable and bounded rather than being rasterized.

Use the constrained `themes/brand-kit.example.json` workflow for local brand
colors and font stacks; arbitrary PowerPoint templates remain out of scope.
