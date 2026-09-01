# Offline reviewed-story Action

The repository includes a composite Action and a reusable workflow definition
that turn a reviewed story file into inspectable CI artifacts without an
AI/network provider. GitHub Actions are temporarily paused, so the reusable
workflow is preserved at `.github/workflows-disabled/review-story.yml` until it
is moved back to `.github/workflows/review-story.yml`. Dependency installation
still uses the normal Python package index; the review step itself only reads
the checked-out story and local assets.

Run the same path locally:

```bash
make review-story
```

The artifact contains:

- deterministic Doctor JSON and Markdown;
- claim-level evidence coverage JSON;
- editable PowerPoint;
- canonical story JSON and Narrative Receipt;
- a manifest that explicitly records `network_provider_used: false` and
  `factual_truth_verified: false`.

After GitHub Actions are restored, call the reusable workflow from another
workflow in this repository:

```yaml
jobs:
  story-review:
    uses: ./.github/workflows/review-story.yml
    with:
      story_path: examples/review.story.md
```

For a normal pull request, the workflow reviews the packaged golden decision
story when relevant story, schema, renderer, or Action files change. A manual
run can select another repository-relative `.json`, `.md`, or `.markdown`
story. Absolute paths, parent traversal, symlinks, unsupported extensions, and
outputs outside the checkout are rejected before review.

The Action diagnoses structure and provenance only. It does not verify factual
truth, open evidence URLs, or transfer story contents to Gemini or another
provider.
