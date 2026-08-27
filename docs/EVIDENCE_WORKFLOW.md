# Evidence workflow

Storyboard Studio records provenance without claiming to verify truth. Every
content slide exposes up to six source entries with:

- label and bounded excerpt/evidence;
- accountable owner;
- one public HTTP(S) URL and/or a relative local reference;
- checked date and optional license;
- explicit `unresolved` or `author-checked` status;
- local claim links such as `summary`, `block-1`, and `block-2`.

URLs with credentials, non-HTTP schemes, localhost, `.local`, private/reserved
IP addresses, absolute paths, and parent traversal are rejected. The product
never fetches a source URL. A valid URL with `unresolved` status remains
unresolved in the coverage view, Doctor, Receipt, and CLI report.

## Author flow

1. Open a slide's **Evidence** editor and add the label/excerpt.
2. Link the entry to one or more claims on that slide.
3. Add an owner and public URL or local relative reference.
4. Review the source yourself, set the checked date, then deliberately choose
   `author-checked`. This status records an author action, not independent fact
   verification.
5. Inspect **Evidence coverage** and leave unsupported claims visibly
   unresolved or revise the deck.
6. Enable **Add citations slide** to append only author-checked entries.

The appendix is native PowerPoint text/shapes and its complete entries also
remain in native slide notes. More than five approved citations create
additional appendix pages rather than shrinking the text silently.

## Automation and preservation

```bash
storyboard evidence examples/fixtures/evidence-edge-cases.json
storyboard evidence examples/fixtures/evidence-edge-cases.json --fail-on-unresolved
storyboard export \
  --input examples/fixtures/evidence-edge-cases.json \
  --output output/evidence.pptx \
  --citations --bundle
```

`POST /api/v1/evidence/coverage` returns slide and claim rows with
`unresolved`, `linked-unresolved`, or `author-checked` status. Full source
objects survive story JSON, deterministic Markdown metadata, slide
copy/duplicate/reorder, import/export, schema-v1 migration, Doctor, Narrative
Receipt, and native PowerPoint notes.

The checked fixture `examples/fixtures/evidence-edge-cases.json` covers Unicode,
long bounded evidence, public and local locators, an unresolved URL, and a
missing owner. `examples/fixtures/evidence-invalid-urls.json` is the rejection
corpus for malicious and private URL forms.
