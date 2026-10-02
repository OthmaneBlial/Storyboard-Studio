# Native measurements

Apple M2, 16 GiB RAM, macOS 26.6, Rust 1.95, release profile.
Measured 2026-10-02T17:06:31.288Z; exact binary hash and source commit are in
[the machine-readable report](apple-m2-macos26.json).

| Slides | Compile | Layout | PPTX + validation |
| ---: | ---: | ---: | ---: |
| 10 | 0.12ms | 5.87ms | 4.73ms |
| 25 | 0.13ms | 0.97ms | 9.74ms |
| 50 | 0.25ms | 1.74ms | 17.84ms |
| 100 | 0.47ms | 3.42ms | 34.44ms |
| 250 | 1.09ms | 8.13ms | 83.56ms |

Five runs per size, arithmetic means. PPTX time includes layout, ZIP compression
and package validation; excludes file I/O, process launch and office rendering.
The first layout group includes font initialization; later groups reuse font state.

CLI warm process startup median: **5.33ms** over 20 launches of
`--version`. First observed launch: **495.7ms**; this is not a
cache-flushed cold boot. Node process-launch overhead is included. Peak RSS for
the complete benchmark process: **48.0 MiB** via macOS time -l.
CLI executable: **7.86 MiB**.

Desktop app bundle: 12.40 MiB; compressed DMG: 5.67 MiB. Desktop startup and RSS
were not measured. No cross-machine or PowerPoint performance comparison is claimed.
Normal background applications remained running. Reproduce on a quiet machine:

```sh
cargo build --release --locked
node scripts/native/measure.mjs
```
