# Curated narrative templates

Templates are deterministic mappings from explicit author fields to story
roles—not prompts and not “AI research”. The versioned packaged catalog makes
the launch boundary inspectable:

```bash
storyboard templates
storyboard templates --all
```

| Template | Status | Narrative contract |
| --- | --- | --- |
| Decision brief | Launched | frame → boundaries → options → trade-off → owned next step |
| Project alignment | Dormant | shared outcome → scope boundary → delivery system → risk review |
| Proposal | Dormant | buyer outcome → bounded approach → choice and proof → commercial decision |
| Incident retrospective | Dormant | impact boundary → evidence timeline → learning, not blame → owned follow-up |

Only the **decision brief** is selectable in the browser and compilable through
the public CLI/API. The three dormant contracts describe required inputs,
deterministic story roles, and an activation gate, but intentionally have no
compiler or UI entry point. External workflow evidence—not a feature-count
goal—must choose which one launches next.

## Launched decision brief

- Structured input: [`examples/briefs/onboarding-decision.json`](../examples/briefs/onboarding-decision.json)
- Job: align a small review group on one bounded decision and next step.
- Evidence assumption: claims, options, sources, and owners are supplied by the
  author; Storyboard Studio does not verify them.

Generate it locally with:

```bash
storyboard compile \
  --input examples/briefs/onboarding-decision.json \
  --output output/onboarding.story.json
storyboard export \
  --input output/onboarding.story.json \
  --output output/onboarding.pptx \
  --bundle
```
