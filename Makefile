.PHONY: check build demo desktop gallery office benchmark site site-check video clean
check:
	cargo fmt --all -- --check
	cargo clippy --workspace --all-targets -- -D warnings
	cargo test --workspace
	npm --prefix apps/desktop run check
build:
	cargo build --release --locked
demo: build
	mkdir -p output
	target/release/storyboard build examples/startup-pitch.md -o output/pitch.pptx --force
	target/release/storyboard verify output/pitch.receipt.json
	target/release/storyboard preview output/pitch.story.json -o output/pitch.html --force
desktop:
	npm --prefix apps/desktop ci
	npm --prefix apps/desktop run tauri -- build
gallery: build
	node scripts/native/generate-gallery.mjs
office:
	node scripts/native/render-gallery.mjs
benchmark: build
	mkdir -p output
	target/release/storyboard benchmark --iterations 5 -o output/benchmark.json --force
site: build
	node scripts/native/prepare-site.mjs
site-check:
	node scripts/native/check-site.mjs
video:
	node scripts/native/make-demo.mjs
clean:
	cargo clean
