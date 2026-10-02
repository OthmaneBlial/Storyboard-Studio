use std::{path::Path, process::Command};
fn cli(root: &Path, args: &[&str]) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_storyboard"))
        .current_dir(root)
        .args(args)
        .output()
        .unwrap()
}
#[test]
fn native_new_compile_build_verify_doctor_and_preview() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();
    for args in [
        &["new", "brief.md"][..],
        &["compile", "brief.md", "-o", "pitch.story.json"],
        &["build", "brief.md", "-o", "pitch.pptx"],
        &["verify", "pitch.receipt.json"],
        &["validate", "pitch.pptx", "--json"],
        &["doctor", "pitch.story.json", "--json"],
        &["preview", "pitch.story.json", "-o", "preview.html"],
        &["diff", "pitch.story.json", "pitch.story.json", "--json"],
    ] {
        let out = cli(root, args);
        assert!(
            out.status.success(),
            "{args:?}: {}",
            String::from_utf8_lossy(&out.stderr)
        );
    }
    assert!(root.join("pitch.pptx").metadata().unwrap().len() > 1000);
    assert!(
        std::fs::read_to_string(root.join("preview.html"))
            .unwrap()
            .contains("<svg")
    );
    let invalid = cli(root, &["build", "brief.md", "-o", "pitch.pptx"]);
    assert!(!invalid.status.success());
    assert!(String::from_utf8_lossy(&invalid.stderr).contains("already exists"));
    let out = cli(root, &["build", "missing.md"]);
    assert!(!out.status.success());
}
