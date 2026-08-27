# Reference-template workflow (opt-in experiment)

The supported branding path is a constrained token file, not arbitrary
PowerPoint reverse engineering:

1. Start from `themes/storyboard-tokens.json` and choose a documented theme.
2. Put only local, permissioned assets under `assets/`.
3. Add each asset to `assets/manifest.json` with checksum, license, and
   attribution; run `make validate-assets`.
4. Generate a fixture and review it in the viewer matrix before sharing.

For colors and fonts, copy `themes/brand-kit.example.json`, then run:

```bash
storyboard brand-kit themes/my-brand.json
storyboard export --input examples/product-brief.json --output output/branded.pptx --brand-kit themes/my-brand.json
```

The same kit can be imported from the browser studio. Brand kits are bounded to
contrast-checked RGB tokens and local font fallback names; they cannot contain
remote URLs, arbitrary CSS, macros, or PowerPoint internals. See
`docs/LAYOUT_CONTRACT.md`.

Missing files, remote URLs, and checksum mismatches fail before rendering. This
keeps a branded deck reproducible and prevents a template from silently
fetching a private or unlicensed asset.
