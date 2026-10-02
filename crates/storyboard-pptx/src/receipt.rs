use crate::{Error, Rendered, Result};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::{io::Write, path::Path};
use storyboard_core::{Story, doctor::Report, theme::Theme};

pub fn sha256(data: &[u8]) -> String {
    format!("{:x}", Sha256::digest(data))
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Artifact {
    pub path: String,
    pub sha256: String,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Receipt {
    pub schema_version: String,
    pub build_version: String,
    pub renderer_version: String,
    pub theme: Theme,
    pub story: Artifact,
    pub presentation: Artifact,
    pub diagnostics: Report,
    pub disclaimer: String,
}
fn filename(path: &Path) -> Result<String> {
    path.file_name()
        .and_then(|n| n.to_str())
        .map(str::to_string)
        .ok_or_else(|| Error::Invalid("Artifact needs a UTF-8 filename".into()))
}
pub fn write_bytes(path: &Path, bytes: &[u8], force: bool) -> Result<()> {
    let parent = path
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .unwrap_or(Path::new("."));
    if path.is_symlink() {
        return Err(Error::Invalid("Refusing to overwrite a symlink".into()));
    }
    let mut temp = tempfile::NamedTempFile::new_in(parent)?;
    temp.write_all(bytes)?;
    temp.as_file().sync_all()?;
    if force {
        temp.persist(path).map_err(|e| e.error)?;
    } else {
        temp.persist_noclobber(path).map_err(|e| e.error)?;
    }
    Ok(())
}
/// Prepare and validate all artifacts before writing. New partial bundles are removed on failure.
pub fn save_bundle(
    story: &Story,
    rendered: &Rendered,
    path: &Path,
    force: bool,
) -> Result<Receipt> {
    if path.extension().is_none_or(|e| e != "pptx") {
        return Err(Error::Invalid("Output must end in .pptx".into()));
    }
    let story_path = path.with_extension("story.json");
    let receipt_path = path.with_extension("receipt.json");
    let story_bytes = serde_json::to_vec_pretty(story)?;
    let receipt=Receipt{schema_version:"3".into(),build_version:storyboard_core::VERSION.into(),renderer_version:"openxml-rust-1".into(),theme:rendered.layout.theme.clone(),story:Artifact{path:filename(&story_path)?,sha256:sha256(&story_bytes)},presentation:Artifact{path:filename(path)?,sha256:sha256(&rendered.pptx)},diagnostics:storyboard_core::diagnose(story),disclaimer:"Hashes establish internal integrity, not authorship, factual truth or viewer compatibility.".into()};
    let receipt_bytes = serde_json::to_vec_pretty(&receipt)?;
    let mut files = vec![
        (path, rendered.pptx.as_slice()),
        (story_path.as_path(), story_bytes.as_slice()),
        (receipt_path.as_path(), receipt_bytes.as_slice()),
    ];
    if !force
        && story_path.exists()
        && !story_path.is_symlink()
        && std::fs::metadata(&story_path)?.len() == story_bytes.len() as u64
        && std::fs::read(&story_path)? == story_bytes
    {
        files.retain(|(p, _)| *p != story_path.as_path());
    }
    for (p, _) in &files {
        if p.is_symlink() || (!force && p.exists()) {
            return Err(Error::Invalid(format!(
                "{} already exists or is a symlink; use --force to replace regular files",
                p.display()
            )));
        }
    }
    let parent = path
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .unwrap_or(Path::new("."));
    // Existing bundles are backed up until all replacements succeed.
    let backup = tempfile::tempdir_in(parent)?;
    let mut saved = Vec::new();
    let mut written = Vec::new();
    let result = (|| -> Result<()> {
        for (i, (p, _)) in files.iter().enumerate() {
            if p.exists() {
                let b = backup.path().join(i.to_string());
                std::fs::rename(p, &b)?;
                saved.push((*p, b));
            }
        }
        for (p, data) in &files {
            write_bytes(p, data, false)?;
            written.push(*p);
        }
        Ok(())
    })();
    if let Err(error) = result {
        for p in written {
            std::fs::remove_file(p)?;
        }
        for (p, b) in saved {
            std::fs::rename(b, p)?;
        }
        return Err(error);
    }
    Ok(receipt)
}
fn artifact_path(root: &Path, artifact: &Artifact) -> Result<std::path::PathBuf> {
    if !storyboard_core::model::safe_relative_path(&artifact.path)
        || Path::new(&artifact.path).components().count() != 1
    {
        return Err(Error::Invalid(
            "Receipt artifacts must be sibling filenames".into(),
        ));
    }
    let path = root.join(&artifact.path).canonicalize()?;
    if !path.starts_with(root) {
        return Err(Error::Invalid(
            "Receipt artifact symlink escapes its directory".into(),
        ));
    }
    Ok(path)
}
pub fn verify(path: &Path) -> Result<Receipt> {
    let meta = std::fs::metadata(path)?;
    if meta.len() > 8 * 1024 * 1024 {
        return Err(Error::Invalid("Receipt exceeds 8 MiB".into()));
    }
    let receipt: Receipt = serde_json::from_slice(&std::fs::read(path)?)?;
    if receipt.schema_version != "3" || receipt.renderer_version != "openxml-rust-1" {
        return Err(Error::Invalid("Unsupported receipt version".into()));
    }
    receipt.theme.validate()?;
    let root = path
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .unwrap_or(Path::new("."))
        .canonicalize()?;
    let mut story_bytes = None;
    for artifact in [&receipt.story, &receipt.presentation] {
        let p = artifact_path(&root, artifact)?;
        let m = std::fs::metadata(&p)?;
        if m.len() > 100 * 1024 * 1024 {
            return Err(Error::Invalid(
                "Artifact exceeds verification budget".into(),
            ));
        }
        let bytes = std::fs::read(p)?;
        if sha256(&bytes) != artifact.sha256 {
            return Err(Error::Invalid(format!(
                "Digest mismatch: {}",
                artifact.path
            )));
        }
        if artifact == &receipt.story {
            story_bytes = Some(bytes);
        } else {
            crate::validate::validate_bytes(&bytes, None)?;
            let mut archive = zip::ZipArchive::new(std::io::Cursor::new(bytes))?;
            let mut theme_xml = String::new();
            use std::io::Read;
            archive
                .by_name("ppt/theme/theme1.xml")?
                .read_to_string(&mut theme_xml)?;
            if theme_xml != crate::xml::theme(&receipt.theme) {
                return Err(Error::Invalid(
                    "Receipt theme differs from the exported theme".into(),
                ));
            }
            let mut custom = String::new();
            archive
                .by_name("docProps/custom.xml")?
                .read_to_string(&mut custom)?;
            if !custom.contains(&format!("<vt:lpwstr>{}</vt:lpwstr>", receipt.story.sha256)) {
                return Err(Error::Invalid(
                    "PPTX is not bound to the receipt's story digest".into(),
                ));
            }
        }
    }
    let story: Story = serde_json::from_slice(
        &story_bytes.ok_or_else(|| Error::Invalid("Missing story".into()))?,
    )?;
    story.validate()?;
    if storyboard_core::diagnose(&story) != receipt.diagnostics {
        return Err(Error::Invalid(
            "Receipt diagnostics differ from the hashed story".into(),
        ));
    }
    storyboard_core::resolve(&story, &receipt.theme)?;
    Ok(receipt)
}
