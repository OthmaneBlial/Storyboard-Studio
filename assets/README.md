# Local asset manifest

Storyboard Studio renders bounded local data and image assets without fetching
remote URLs. The checked-in `demo/` fixture proves native bar, line, and donut
charts plus a local SVG workflow:

- keep files local and commit only synthetic or permissioned assets;
- list every file in `manifest.json` with a SHA-256 checksum, license, and
  attribution;
- reject URLs, missing files, checksum mismatches, oversized/unreadable images,
  malformed data, and SVGs with active or external content before rendering;
- never download or cache a remote asset implicitly.

Validate the manifest with `make validate-assets`. To render the complete
fixture with paths resolved relative to the outline:

```bash
storyboard export \
  --input assets/demo/native-visuals.json \
  --output output/native-visuals.pptx
```

Data files are limited to 256 KB, eight columns, and twelve chart rows. Charts
support one category field, up to three numeric value fields, and the native
PowerPoint bar, line, or donut types. Images are limited to 5 MB and 20
megapixels. PNG and JPEG files are embedded locally; safe SVG files are
rasterized locally after the SVG is checked for scripts, animation, entities,
and non-local references. The original checksum, license, attribution, source
note, and alt text remain in the story, browser evidence panel, slide notes,
and Narrative Receipt.

Generative image providers are deliberately outside the core. Any future
provider must be an explicit optional adapter and may never receive local
evidence or assets without a separate user action.
