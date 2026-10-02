use crate::{Error, Result};
use std::{
    collections::BTreeMap,
    io::{Cursor, Write},
    path::Path,
};
use storyboard_core::{
    layout::Rect,
    model::{Image, ImageFit},
};
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};

pub const REL_NS: &str = "http://schemas.openxmlformats.org/officeDocument/2006/relationships";
pub const PACKAGE_REL_NS: &str = "http://schemas.openxmlformats.org/package/2006/relationships";
#[derive(Clone)]
pub struct Relationship {
    pub id: String,
    pub kind: String,
    pub target: String,
    pub external: bool,
}
pub fn relationship(id: impl Into<String>, kind: &str, target: impl Into<String>) -> Relationship {
    Relationship {
        id: id.into(),
        kind: kind.into(),
        target: target.into(),
        external: false,
    }
}
pub fn rels(items: &[Relationship]) -> String {
    let mut xml = format!(
        "{}<Relationships xmlns=\"{PACKAGE_REL_NS}\">",
        crate::xml::HEADER
    );
    for r in items {
        let mode = if r.external {
            " TargetMode=\"External\""
        } else {
            ""
        };
        let kind = if r.kind.starts_with("http") {
            r.kind.clone()
        } else {
            format!("{REL_NS}/{}", r.kind)
        };
        xml.push_str(&format!(
            "<Relationship Id=\"{}\" Type=\"{}\" Target=\"{}\"{mode}/>",
            crate::xml::escape(&r.id),
            crate::xml::escape(&kind),
            crate::xml::escape(&r.target)
        ));
    }
    xml.push_str("</Relationships>");
    xml
}
pub fn zip(parts: &BTreeMap<String, Vec<u8>>) -> Result<Vec<u8>> {
    let mut archive = ZipWriter::new(Cursor::new(Vec::new()));
    let options = SimpleFileOptions::default()
        .compression_method(CompressionMethod::Deflated)
        .last_modified_time(zip::DateTime::default());
    for (name, bytes) in parts {
        archive.start_file(name, options)?;
        archive.write_all(bytes)?;
    }
    Ok(archive.finish()?.into_inner())
}
pub struct Asset {
    pub data: Vec<u8>,
    pub extension: &'static str,
    pub width: u32,
    pub height: u32,
}
pub fn asset(root: &Path, image: &Image) -> Result<Asset> {
    if !storyboard_core::model::safe_relative_path(&image.path) {
        return Err(Error::Invalid("Image path must be relative".into()));
    }
    let root = root.canonicalize()?;
    let path = root.join(&image.path).canonicalize()?;
    if !path.starts_with(&root) {
        return Err(Error::Invalid(
            "Image symlink escapes project directory".into(),
        ));
    }
    let meta = std::fs::metadata(&path)?;
    if !meta.is_file() || meta.len() > 20 * 1024 * 1024 {
        return Err(Error::Invalid(
            "Image must be a regular file ≤20 MiB".into(),
        ));
    }
    let data = std::fs::read(&path)?;
    let format =
        image::guess_format(&data).map_err(|e| Error::Invalid(format!("Invalid image: {e}")))?;
    let extension = match format {
        image::ImageFormat::Png => "png",
        image::ImageFormat::Jpeg => "jpeg",
        _ => {
            return Err(Error::Invalid(
                "Only local PNG/JPEG images are supported".into(),
            ));
        }
    };
    let reader = image::ImageReader::with_format(Cursor::new(&data), format);
    let (width, height) = reader
        .into_dimensions()
        .map_err(|e| Error::Invalid(format!("Invalid image dimensions: {e}")))?;
    if width == 0
        || height == 0
        || width > 16_384
        || height > 16_384
        || width as u64 * height as u64 > 50_000_000
    {
        return Err(Error::Invalid("Image dimensions exceed safe limits".into()));
    }
    Ok(Asset {
        data,
        extension,
        width,
        height,
    })
}
pub fn image_geometry(rect: Rect, image: &Image, asset: &Asset) -> (Rect, String) {
    let ratio = asset.width as f64 / asset.height as f64;
    let box_ratio = rect.width / rect.height;
    if image.fit == ImageFit::Contain {
        let (w, h) = if ratio > box_ratio {
            (rect.width, rect.width / ratio)
        } else {
            (rect.height * ratio, rect.height)
        };
        (
            Rect {
                x: rect.x + (rect.width - w) / 2.0,
                y: rect.y + (rect.height - h) / 2.0,
                width: w,
                height: h,
            },
            String::new(),
        )
    } else {
        let (horizontal, vertical) = if ratio > box_ratio {
            ((1.0 - box_ratio / ratio) * 50_000.0, 0.0)
        } else {
            (0.0, (1.0 - ratio / box_ratio) * 50_000.0)
        };
        (
            rect,
            format!(
                "<a:srcRect l=\"{}\" r=\"{}\" t=\"{}\" b=\"{}\"/>",
                horizontal.round() as i64,
                horizontal.round() as i64,
                vertical.round() as i64,
                vertical.round() as i64
            ),
        )
    }
}
