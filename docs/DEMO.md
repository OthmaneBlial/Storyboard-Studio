# Reproduce the native walkthrough

The published 49-second walkthrough is an edited sequence of observed production
screens, actual recorded CLI stdout, and the current nine-slide deck imported in
Keynote. It is not a continuous screen recording. All content is synthetic.
The caption track is embedded in MP4 and supplied as WebVTT for the website.

1. Run `make check`, `make demo` and `make desktop`.
2. Open the production bundle. Capture the brief editor, Story Map, Doctor, themes
   and preview into `docs/screenshots/native/{editor,story-map,doctor,themes,preview}.png`.
   Use the application's native commands and capture only its window.
3. Record actual `storyboard --version`, build and receipt-verification output.
   The CLI image is a styled transcript of stdout; it is explicitly labeled.
4. Export via the native file dialog. Verify its sibling receipt with the CLI.
5. Open a current gallery deck in a real office viewer. Capture the selected
   editable title/object. This run uses `keynote.png`; PowerPoint remains unverified.
6. Run `node scripts/native/make-demo.mjs` with FFmpeg/ffprobe installed.

Outputs: `output/demo/storyboard-native-walkthrough.mp4`, captions, normalized
frames and probe metadata. The script checks 49-second duration, 1280×720 size and
uses H.264/yuv420p for browser playback. Keep the source screenshots and this script
in Git; put larger continuous recordings in GitHub release assets.

The current gallery artifact's hash and viewer limitations are recorded in
[compatibility observations](COMPATIBILITY.md). Recapture screens after meaningful
UI changes before regenerating a new walkthrough.
