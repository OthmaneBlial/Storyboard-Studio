# Portable projects with actual local files

A project ZIP contains `deck.story.json`, the exact declared asset files, and
`project.json` with SHA-256 hashes and a format version. A review bundle also
contains a generated `deck.pptx` and its integrity receipt. External evidence
references are listed in the manifest but are never fetched or embedded.
Hashes detect internal inconsistency; they do not authenticate the author or
verify source accuracy.

## Browser workflow

1. Build or open a story. Expand **Local images and chart data**.
2. Select a CSV, JSON, PNG, JPEG or SVG file. Supply license/permission,
   attribution, and image alt text or a data source note.
3. **Validate and attach file** checks its actual bytes on the local server.
4. Choose the asset and target slide. For a chart, explicitly choose its category
   column, numeric value column and chart type, then **Use asset on slide**.
   Invalid values or unknown columns produce an error without changing the slide.
5. Use **Save project ZIP + assets** to preserve the files. Plain **Save project
   JSON** stores their references only and cannot confirm a complete asset save.
6. Open the ZIP with **Open saved project** from a fresh tab. The same assets can
   be rendered from that tab; the server's working directory is irrelevant.

The target slide's previous block is replaced only after validation. Undo restores
it. Saving a project does not require PowerPoint rendering, but the story and
asset formats must be valid. A save/export request uses a snapshot; subsequent
editor changes remain in the tab. A cancelled file selection does nothing.

The source checkbox affects portable ZIP and review-bundle downloads. Unchecking
it removes slide evidence entries, decision-brief evidence, Doctor dispositions
and author-edit logs from the downloaded copy, and disables the citations
appendix. The current story is unchanged and is **not** marked saved by that
redacted copy. Brief text, slide text, speaker notes, chart data, images and asset
attribution/source notes remain included and can still be sensitive. This is not
a general anonymizer; review the output before sharing it.

## CLI workflow

```sh
storyboard project pack --input my-project/story.json --output my-project.zip
storyboard project open --input my-project.zip --output reopened-project
storyboard export --input reopened-project/deck.story.json --output regenerated.pptx --bundle
```

`pack --render` includes a real PowerPoint and receipt in the ZIP.
`pack --without-sources` produces the source-entry-free copy described above.
Packing reads only asset paths explicitly declared by the input story, relative
to that story's directory. Symlink assets are rejected. Existing output files or
extraction directories are never overwritten. `open` restores editable inputs;
the original rendered PPTX/receipt remain in the ZIP. The final command generates
a fresh PPTX/receipt for the reopened inputs.

This workflow has been tested on macOS ARM64 / Python 3.14. Windows and Linux
execution remain release gates. Atomic archive publication uses a hard link on
the output filesystem; a filesystem without hard-link support returns an error
rather than falling back to an unsafe overwrite.

## Bounds and supported formats

- At most 12 assets and 4,000,000 combined decoded asset bytes. Existing stricter
  per-format, pixel, row, column and SVG limits also apply.
- Story JSON at most 200,000 bytes. Project ZIP at most 8,000,000 bytes, 24 regular
  members and 12,000,000 total declared uncompressed bytes.
- Five explicit project POST routes accept at most 8,000,000 HTTP body bytes to
  accommodate base64 or ZIP data. Other HTTP routes remain at 200,000 bytes.
  The same Host/Origin, deadline and four-active-request controls apply.
- Duplicate/case-colliding members, traversal, absolute paths, symlinks, encrypted
  entries, platform-reserved names, undeclared files and bad hashes are rejected.
- CSV uses a header row. JSON uses an array of row objects or `{ "rows": [...] }`.
  Images use the already supported decoder and pixel bounds. SVG must use UTF-8
  and requires the
  optional SVG extra and native Cairo; active content, CSS styles and escaped
  attribute values are unsupported. Use simple presentation attributes or PNG.

Asset bytes stay in tab memory; no browser storage is enabled. Up to 16 MB may be
retained for undo/history across projects in a tab, even after an asset is no
longer used. Save and reopen in a fresh tab to clear that history. Local validation
uses temporary directories removed after the operation. Downloadable server
ZIP/PPTX copies follow the existing 24-hour export-cache lifetime.
