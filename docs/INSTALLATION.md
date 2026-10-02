# Installation

## CLI from source

Install Rust 1.95+ through rustup, clone this repository, then run:

```bash
cargo build --release --locked
./target/release/storyboard build examples/startup-pitch.md -o pitch.pptx
./target/release/storyboard verify pitch.receipt.json
```

The CLI binary is `target/release/storyboard` (`storyboard.exe` on Windows).
`cargo install --path crates/storyboard-cli --locked` installs it on your local PATH.
No crates.io publication or Homebrew formula is claimed for this native preview.

## Desktop from source

Install Node 20+, Rust and your platform's official
[Tauri prerequisites](https://v2.tauri.app/start/prerequisites/).

```bash
npm --prefix apps/desktop ci
npm --prefix apps/desktop run tauri -- build
```

Bundles are written beneath `target/release/bundle/`. Node is authoring/build
tooling; the compiled app uses the operating system WebView. Targets are macOS
Apple Silicon/Intel, Windows x64 and Linux x64. A target is not certified until its
actual binary and installer have been built and checked on that platform.

Use the [GitHub releases](https://github.com/OthmaneBlial/Storyboard-Studio/releases)
for published downloads, and check that a listed release is native 0.3 or newer.
Older releases belong to the retired generation.
