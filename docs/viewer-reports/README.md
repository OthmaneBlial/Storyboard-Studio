# Versioned viewer reports

These reports preserve release-candidate evidence that a named viewer opened
and rendered the checked-in fixtures. Each JSON record pins the viewer and
platform, the source-fixture SHA-256, page count, inspection notes, and a
committed contact sheet. A report is not a claim of universal PowerPoint,
Keynote, or Google Slides parity.

Validate the evidence without launching a viewer:

```bash
make validate-viewer-reports
```

To refresh the LibreOffice report, run the exact commands recorded in its
`fixtures[*].command` fields with `--require`, inspect every rendered page,
replace the contact sheet only when the result is still a PASS, and update the
report's source and screenshot digests. Keep a new report filename when the
viewer version or platform changes; never overwrite a report to hide a
regression.

Current evidence:

- [`libreoffice-26.8.0.3-macos-26.0.json`](libreoffice-26.8.0.3-macos-26.0.json)
  — LibreOffice Impress 26.8.0.3 on macOS 26.0 / Apple Silicon.
- [`assets/libreoffice-product-brief.png`](assets/libreoffice-product-brief.png)
  — four-page product fixture.
- [`assets/libreoffice-semantic-midnight.png`](assets/libreoffice-semantic-midnight.png)
  and [`assets/libreoffice-semantic-glacier.png`](assets/libreoffice-semantic-glacier.png)
  — eight typed blocks in dark and light themes.
- [`assets/libreoffice-native-visuals.png`](assets/libreoffice-native-visuals.png)
  — native charts and a local image.
- [`assets/libreoffice-evidence.png`](assets/libreoffice-evidence.png)
  — evidence and citations edge cases.
