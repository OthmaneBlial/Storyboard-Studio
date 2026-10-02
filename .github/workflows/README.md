# GitHub Actions paused

The owner requested GitHub CI disabled on 2026-10-02. All four repository
workflows are disabled through GitHub and their current definitions are
preserved byte-for-byte in `../workflows-disabled/2026-10-rust-migration/`.
There are no active YAML workflows here. Earlier snapshots remain untouched.

Run native checks locally before each completed milestone:

```sh
cargo fmt --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
```

Frontend checks and generated-deck validation are required when those paths
change. Do not restore or re-enable GitHub CI without an explicit owner request.
Archived Python workflows are historical references, not Rust release jobs.
