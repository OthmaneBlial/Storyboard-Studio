# Native release preparation

Run `make check`, `cargo build --release --locked`, the documented consumer example,
and the desktop UI smoke check on the platform being published. GitHub CI stays off.
Build locally; never label a cross-compiled artifact as runtime-tested.

| Platform | Rust target | Desktop package | Current 0.3 evidence |
| --- | --- | --- | --- |
| macOS Apple Silicon | aarch64-apple-darwin | .dmg | Built and exercised locally |
| macOS Intel | x86_64-apple-darwin | .dmg | Prepared; no native runtime check |
| Windows x64 | x86_64-pc-windows-msvc | .msi / .exe | Prepared; no native build/runtime check |
| Linux x64 | x86_64-unknown-linux-gnu | .AppImage / .deb | Prepared; no native build/runtime check |

On each native host with Rust 1.95+, Node 20+ and the
[Tauri prerequisites](https://v2.tauri.app/start/prerequisites/):

```sh
cargo build --release --locked
npm --prefix apps/desktop ci
npm --prefix apps/desktop run tauri -- build
node scripts/native/package-release.mjs
```

The packaging script uses the compiler's host target and includes only locally
present installers. Run in a fresh checkout per platform to avoid stale bundles.
Outputs in `output/releases/v0.3.0/` include the CLI archive with an example and
license, installers, a build manifest and SHA256SUMS. Extract the archive in a fresh
directory, run its CLI `--version`, build the included startup example, and verify
the resulting receipt before uploading. Compare the downloaded bytes after upload.

macOS 0.3.0 is an ad-hoc signed developer preview, without a Developer ID or
notarization. No signing credential is stored in source. Public signing/notarization
requires the owner's Apple developer identity; Windows signing is likewise separate.
Do not silently bypass system trust warnings during automated testing.

Publish actual assets, not target names without binaries:

```sh
gh release create v0.3.0 --target main --prerelease \
  --title '0.3.0 — native Rust and Tauri preview' --notes-file output/release-notes.md
gh release upload v0.3.0 output/releases/v0.3.0/*.tar.gz \
  output/releases/v0.3.0/*.dmg output/releases/v0.3.0/SHA256SUMS \
  output/releases/v0.3.0/build-manifest.json
```

The example upload command is for the observed macOS build. Use only the installer
extensions actually produced on the other hosts. Registry and Homebrew publication
remain separate; `cargo install --path crates/storyboard-cli --locked` works now.
