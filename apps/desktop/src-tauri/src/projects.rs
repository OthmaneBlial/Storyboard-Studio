use serde::Serialize;
use std::path::{Path, PathBuf};
#[cfg(test)]
use storyboard_core::Theme;

pub use storyboard_core::Project;
#[derive(Serialize)]
pub struct Recent {
    pub id: String,
    pub title: String,
    pub updated_ms: u64,
    pub slides: usize,
    pub theme: String,
}
fn project_path(root: &Path, id: &str) -> Result<PathBuf, String> {
    if id.is_empty() || id.len() > 80 || !id.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-')
    {
        return Err("Invalid project identifier".into());
    }
    Ok(root.join(format!("{id}.storyboard")))
}
pub fn save(root: &Path, project: &Project, asset_root: &Path) -> Result<(), String> {
    std::fs::create_dir_all(root).map_err(|e| e.to_string())?;
    let mut project = project.clone();
    project.story = storyboard_pptx::assets::portable_story(&project.story, asset_root, root)
        .map_err(|e| e.to_string())?;
    project.validate().map_err(|e| e.to_string())?;
    let bytes = serde_json::to_vec_pretty(&project).map_err(|e| e.to_string())?;
    if bytes.len() > 16 * 1024 * 1024 {
        return Err("Project exceeds 16 MiB".into());
    }
    std::fs::create_dir_all(root).map_err(|e| e.to_string())?;
    storyboard_pptx::receipt::write_bytes(&project_path(root, &project.id)?, &bytes, true)
        .map_err(|e| e.to_string())
}
pub fn load(root: &Path, id: &str) -> Result<Project, String> {
    let path = project_path(root, id)?;
    if path.is_symlink() {
        return Err("Project symlinks are not allowed".into());
    }
    let size = std::fs::metadata(&path).map_err(|e| e.to_string())?.len();
    if size > 16 * 1024 * 1024 {
        return Err("Project exceeds 16 MiB".into());
    }
    let project: Project = serde_json::from_slice(&std::fs::read(path).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    if project.project_version != 1 || project.id != id {
        return Err("Project version or identifier mismatch".into());
    }
    project.validate().map_err(|e| e.to_string())?;
    Ok(project)
}
pub fn recent(root: &Path) -> Result<Vec<Recent>, String> {
    if !root.exists() {
        return Ok(Vec::new());
    }
    let mut items = Vec::new();
    for entry in std::fs::read_dir(root)
        .map_err(|e| e.to_string())?
        .take(500)
    {
        let entry = entry.map_err(|e| e.to_string())?;
        let path = entry.path();
        if path.extension().is_some_and(|x| x == "storyboard")
            && let Some(id) = path.file_stem().and_then(|x| x.to_str())
        {
            let p = load(root, id)?;
            items.push(Recent {
                id: p.id,
                title: p.story.presentation.title,
                updated_ms: p.updated_ms,
                slides: p.story.presentation.slides.len(),
                theme: p.theme.name,
            });
        }
    }
    items.sort_by_key(|p| std::cmp::Reverse(p.updated_ms));
    Ok(items)
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn local_autosave_roundtrip_and_escape_rejection() {
        let root = tempfile::tempdir().unwrap();
        let story =
            storyboard_core::compile(include_str!("../../../../examples/startup-pitch.md"), true)
                .unwrap();
        let p = Project {
            project_version: 1,
            id: "project-123".into(),
            brief: "source".into(),
            story,
            theme: Theme::named("midnight").unwrap(),
            updated_ms: 123,
        };
        save(root.path(), &p, root.path()).unwrap();
        assert_eq!(load(root.path(), &p.id).unwrap().story, p.story);
        assert_eq!(recent(root.path()).unwrap().len(), 1);
        assert!(load(root.path(), "../../escape").is_err());
        let mut invalid = p;
        invalid.story.schema_version = "100".into();
        assert!(save(root.path(), &invalid, root.path()).is_err());
    }
}
