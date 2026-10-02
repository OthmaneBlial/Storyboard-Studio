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

#[test]
fn custom_desktop_projects_build_preview_and_inspect_through_cli() {
    let dir = tempfile::tempdir().unwrap();
    let mut story =
        storyboard_core::compile(include_str!("../../../examples/startup-pitch.md"), true).unwrap();
    let mut theme = storyboard_core::Theme::named("minimal").unwrap();
    theme.name = "my-local-brand".into();
    story.presentation.theme = theme.name.clone();
    let project = storyboard_core::Project {
        project_version: 1,
        id: "project-custom".into(),
        brief: "Local custom theme".into(),
        story,
        theme,
        updated_ms: 123,
    };
    std::fs::write(
        dir.path().join("custom.storyboard"),
        serde_json::to_vec(&project).unwrap(),
    )
    .unwrap();
    for args in [
        &["build", "custom.storyboard", "-o", "custom.pptx"][..],
        &["preview", "custom.storyboard", "--svg", "-o", "custom.svg"],
        &["inspect", "custom.storyboard", "--layout"],
        &["verify", "custom.receipt.json"],
    ] {
        let out = cli(dir.path(), args);
        assert!(
            out.status.success(),
            "{args:?}: {}",
            String::from_utf8_lossy(&out.stderr)
        );
    }
}

#[test]
fn draft_command_requires_explicit_transmission_approval() {
    let dir = tempfile::tempdir().unwrap();
    std::fs::write(dir.path().join("brief.md"), "author owned input").unwrap();
    let out = cli(
        dir.path(),
        &[
            "draft",
            "brief.md",
            "--endpoint",
            "http://127.0.0.1:1/v1/chat/completions",
            "--model",
            "fixture",
        ],
    );
    assert!(!out.status.success());
    assert!(String::from_utf8_lossy(&out.stderr).contains("Explicit approval"));
}
