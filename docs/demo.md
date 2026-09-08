# Accessible transcript for the local workflow demo

This is the accessible transcript for the canonical
[31-second private AI app-only proof recording](assets/storyboard-demo-ai.mp4). A [20-second social cut](assets/storyboard-demo-ai-short.mp4) is also available. It uses only the
synthetic checked-in private AI brief and local compiler; no API key or network
provider is required. The recording never launches PowerPoint, LibreOffice, or
another Office application.

1. `make setup && make run`
2. Open `http://127.0.0.1:8000`.
3. Choose **Try a sample brief**, then select **Build decision story**. The sample is the private AI review-loop brief.
4. Run **Narrative Doctor**. Accept the missing evidence-owner action, add the
   owner, and rerun the structural review.
5. Review the story map and the editable content frames.
6. Select **Export PowerPoint** and download the native PPTX.
7. The video ends on the download confirmation and the AI deck poster. The
   committed [`product-brief-ai.pptx`](fixtures/product-brief-ai.pptx) is a
   matching native editable preview; its text objects can be inspected with
   the repository's headless `python-pptx` checks.

For a terminal-only health check, run `make smoke`. It starts an ephemeral
local server, exercises both API endpoints, validates the downloaded ZIP
signature, and removes its temporary export before exiting.

The recording is product proof on the maintainer's machine, not external-user
evidence. The existing onboarding recording remains available as a historical
artifact at [`storyboard-demo-app-only.mp4`](assets/storyboard-demo-app-only.mp4).
The full reproducible artifact set, including versioned stories and verified
Narrative Receipts, is in the [golden gallery](../gallery/README.md).
