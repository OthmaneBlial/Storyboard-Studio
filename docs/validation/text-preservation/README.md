# Full text: targeted LibreOffice check

This synthetic fixture exposed two overlaps after removing text slicing: the
main heading touched the summary and the repeated side title touched decorative
illustrations. The after image comes from a fresh render of the same fixture.

- [Before](before.png)
- [After](after.png)
- [Exact scope and renderer hashes](report.json)
- [Reproducible input](fixture.json)

Render the fixture with `storyboard_studio.renderer.create_presentation` (the
top-level `generate_pptx` import remains a compatibility path), then convert the
result with LibreOffice to PDF using an isolated `UserInstallation` profile.
Rasterize PDF page 2 with `pdftoppm -f 2 -singlefile -scale-to 1440 -png`.
The report records the viewer version. No private user content was used.

This is one inspected page, not a claim that every layout fits or that the deck
was edited interactively in LibreOffice or PowerPoint. The original default font
substitution remains visible and needs broader viewer review.
