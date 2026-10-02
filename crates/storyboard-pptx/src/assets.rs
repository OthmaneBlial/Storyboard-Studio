//! Content-addressed image sidecars keep projects and exported stories portable.
use crate::{Error, Result, package, receipt};
use std::{collections::BTreeMap, path::Path};
use storyboard_core::{Block, Story};

/// Copy validated local images beneath `destination` and return remapped story paths.
/// Move the `assets` directory with a project/story JSON when sharing it.
pub fn portable_story(story: &Story, source: &Path, destination: &Path) -> Result<Story> {
    story.validate()?;
    let mut story = story.clone();
    let mut files = BTreeMap::new();
    let mut total = 0usize;
    fn visit(
        blocks: &mut [Block],
        source: &Path,
        files: &mut BTreeMap<String, Vec<u8>>,
        total: &mut usize,
    ) -> Result<()> {
        for block in blocks {
            match block {
                Block::Image { image } => {
                    let asset = package::asset(source, image)?;
                    let name = format!("{}.{}", receipt::sha256(&asset.data), asset.extension);
                    if !files.contains_key(&name) {
                        *total += asset.data.len();
                        if *total > 100 * 1024 * 1024 {
                            return Err(Error::Invalid("Project images exceed 100 MiB".into()));
                        }
                        files.insert(name.clone(), asset.data);
                    }
                    image.path = format!("assets/{name}");
                }
                Block::Group { children, .. } => visit(children, source, files, total)?,
                Block::Positioned { block, .. } => {
                    visit(std::slice::from_mut(block.as_mut()), source, files, total)?
                }
                _ => {}
            }
        }
        Ok(())
    }
    for slide in &mut story.presentation.slides {
        visit(&mut slide.blocks, source, &mut files, &mut total)?;
    }
    if files.is_empty() {
        return Ok(story);
    }
    let destination = destination.canonicalize()?;
    let assets = destination.join("assets");
    if assets.is_symlink() {
        return Err(Error::Invalid(
            "Asset destination cannot be a symlink".into(),
        ));
    }
    std::fs::create_dir_all(&assets)?;
    for (name, data) in files {
        let path = assets.join(name);
        if path.is_symlink() {
            return Err(Error::Invalid("Asset cannot be a symlink".into()));
        }
        if path.exists() {
            if std::fs::metadata(&path)?.len() != data.len() as u64 || std::fs::read(&path)? != data
            {
                return Err(Error::Invalid("Content-addressed asset has changed".into()));
            }
        } else {
            receipt::write_bytes(&path, &data, false)?;
        }
    }
    Ok(story)
}

pub fn export(
    story: &Story,
    theme: &storyboard_core::Theme,
    source: &Path,
    output: &Path,
    force: bool,
) -> Result<receipt::Receipt> {
    let destination = output
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .unwrap_or(Path::new("."));
    let story = portable_story(story, source, destination)?;
    let rendered = crate::render(&story, theme, destination)?;
    receipt::save_bundle(&story, &rendered, output, force)
}
