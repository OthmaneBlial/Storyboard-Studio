//! Bounded package checks for generated OpenXML. Does not certify viewer fidelity.
use crate::{Error, Result};
use quick_xml::{NsReader, events::Event, name::ResolveResult};
use serde::Serialize;
use std::{
    collections::{BTreeMap, BTreeSet},
    io::{Cursor, Read},
    path::Path,
};
#[derive(Debug, Serialize)]
pub struct Validation {
    pub slides: usize,
    pub parts: usize,
    pub relationships: usize,
    pub media: usize,
    pub text: Vec<String>,
    pub scope: String,
}
#[derive(Default)]
struct XmlInfo {
    rels: Vec<(String, String, bool)>,
    references: Vec<String>,
    text: Vec<String>,
    slide_count: usize,
}
fn parse(bytes: &[u8], name: &str) -> Result<XmlInfo> {
    let mut reader = NsReader::from_reader(bytes);
    let mut info = XmlInfo::default();
    let mut depth = 0usize;
    let mut roots = 0;
    let mut capture = false;
    let mut current_text = String::new();
    loop {
        let (namespace, event) = reader
            .read_resolved_event()
            .map_err(|e| Error::Invalid(format!("Malformed XML {name}: {e}")))?;
        if matches!(namespace, ResolveResult::Unknown(_)) {
            return Err(Error::Invalid(format!("Unbound XML namespace in {name}")));
        }
        match event {
            Event::Start(e) | Event::Empty(e) => {
                let empty =
                    bytes.get(reader.buffer_position().saturating_sub(2) as usize) == Some(&b'/');
                if depth == 0 {
                    roots += 1;
                }
                if !empty {
                    depth += 1;
                }
                if e.name().as_ref() == b"a:t" {
                    capture = true;
                    current_text.clear();
                }
                if e.name().as_ref() == b"p:sldId" {
                    info.slide_count += 1;
                }
                let mut id = None;
                let mut target = None;
                let mut external = false;
                for a in e.attributes() {
                    let a = a.map_err(|e| Error::Invalid(format!("XML attribute {name}: {e}")))?;
                    if matches!(reader.resolve_attribute(a.key).0, ResolveResult::Unknown(_)) {
                        return Err(Error::Invalid(format!(
                            "Unbound XML attribute namespace in {name}"
                        )));
                    }
                    let value = a
                        .decode_and_unescape_value(reader.decoder())
                        .map_err(|e| Error::Invalid(e.to_string()))?
                        .into_owned();
                    match a.key.as_ref() {
                        b"Id" => id = Some(value),
                        b"Target" => target = Some(value),
                        b"TargetMode" => external = value == "External",
                        b"r:id" | b"r:embed" | b"r:link" => info.references.push(value),
                        _ => {}
                    }
                }
                if e.name().as_ref() == b"Relationship" {
                    info.rels.push((
                        id.ok_or_else(|| Error::Invalid(format!("Relationship lacks ID: {name}")))?,
                        target.ok_or_else(|| {
                            Error::Invalid(format!("Relationship lacks target: {name}"))
                        })?,
                        external,
                    ));
                }
                if empty && e.name().as_ref() == b"a:t" {
                    capture = false;
                }
            }
            Event::End(e) => {
                depth = depth
                    .checked_sub(1)
                    .ok_or_else(|| Error::Invalid(format!("Unbalanced XML {name}")))?;
                if e.name().as_ref() == b"a:t" {
                    capture = false;
                    info.text.push(std::mem::take(&mut current_text));
                }
            }
            Event::Text(e) => {
                let decoded = e.xml_content().map_err(|e| Error::Invalid(e.to_string()))?;
                let text = quick_xml::escape::unescape(&decoded)
                    .map_err(|e| Error::Invalid(e.to_string()))?
                    .into_owned();
                if capture {
                    current_text.push_str(&text);
                } else if depth == 0 && !text.trim().is_empty() {
                    return Err(Error::Invalid(format!("Text outside XML root: {name}")));
                }
            }
            Event::GeneralRef(e) => {
                let name = e.decode().map_err(|e| Error::Invalid(e.to_string()))?;
                let entity = format!("&{name};");
                let value = quick_xml::escape::unescape(&entity)
                    .map_err(|e| Error::Invalid(e.to_string()))?;
                if capture {
                    current_text.push_str(&value);
                }
            }
            Event::DocType(_) => return Err(Error::Invalid("XML DTDs are forbidden".into())),
            Event::Eof => break,
            _ => {}
        }
    }
    if roots != 1 || depth != 0 {
        return Err(Error::Invalid(format!(
            "XML needs one balanced root: {name}"
        )));
    }
    Ok(info)
}
fn owner(rels: &str) -> String {
    if rels == "_rels/.rels" {
        return String::new();
    }
    rels.replace("/_rels/", "/")
        .trim_end_matches(".rels")
        .into()
}
fn target_path(owner: &str, target: &str) -> Result<String> {
    if target.contains(['\\', ':', '#', '?']) {
        return Err(Error::Invalid("Unsafe internal relationship target".into()));
    }
    let mut segments = if target.starts_with('/') {
        Vec::new()
    } else {
        owner
            .rsplit_once('/')
            .map(|(dir, _)| dir.split('/').map(str::to_string).collect())
            .unwrap_or_default()
    };
    for part in target.split('/') {
        match part {
            "" | "." => {}
            ".." => {
                if segments.pop().is_none() {
                    return Err(Error::Invalid("Relationship escapes package".into()));
                }
            }
            _ => segments.push(part.into()),
        }
    }
    Ok(segments.join("/"))
}
pub fn validate_bytes(bytes: &[u8], expected_slides: Option<usize>) -> Result<Validation> {
    if bytes.len() > 100 * 1024 * 1024 {
        return Err(Error::Invalid("PPTX exceeds 100 MiB".into()));
    }
    let mut archive = zip::ZipArchive::new(Cursor::new(bytes))?;
    if archive.len() > 4096 {
        return Err(Error::Invalid("PPTX has too many parts".into()));
    }
    let mut parts = BTreeMap::new();
    let mut total = 0u64;
    for i in 0..archive.len() {
        let mut entry = archive.by_index(i)?;
        let name = entry.name().to_string();
        if !storyboard_core::model::safe_relative_path(&name) || parts.contains_key(&name) {
            return Err(Error::Invalid(
                "Unsafe or duplicate archive part name".into(),
            ));
        }
        if entry.size() > 32 * 1024 * 1024 {
            return Err(Error::Invalid("Archive part exceeds 32 MiB".into()));
        }
        total += entry.size();
        if total > 200 * 1024 * 1024 {
            return Err(Error::Invalid(
                "Archive decompression budget exceeded".into(),
            ));
        }
        let mut data = Vec::new();
        entry
            .by_ref()
            .take(32 * 1024 * 1024 + 1)
            .read_to_end(&mut data)?;
        if data.len() > 32 * 1024 * 1024 {
            return Err(Error::Invalid("Archive part expanded beyond limit".into()));
        }
        parts.insert(name, data);
    }
    for required in [
        "[Content_Types].xml",
        "_rels/.rels",
        "ppt/presentation.xml",
        "ppt/_rels/presentation.xml.rels",
        "ppt/theme/theme1.xml",
    ] {
        if !parts.contains_key(required) {
            return Err(Error::Invalid(format!("Missing required part {required}")));
        }
    }
    let mut infos = BTreeMap::new();
    for (name, data) in &parts {
        if name.ends_with(".xml") || name.ends_with(".rels") {
            infos.insert(name.clone(), parse(data, name)?);
        }
    }
    let mut relationship_count = 0;
    for (name, info) in infos.iter().filter(|(n, _)| n.ends_with(".rels")) {
        let parent = owner(name);
        if !parent.is_empty() && !parts.contains_key(&parent) {
            return Err(Error::Invalid(format!(
                "Relationship file has no owning part: {name}"
            )));
        }
        let mut ids = BTreeSet::new();
        for (id, target, external) in &info.rels {
            relationship_count += 1;
            if id.is_empty() || !ids.insert(id) {
                return Err(Error::Invalid(format!(
                    "Duplicate/empty relationship ID: {name}"
                )));
            }
            if *external {
                if !storyboard_core::model::valid_url(target) {
                    return Err(Error::Invalid("Unsafe external relationship".into()));
                }
            } else {
                let resolved = target_path(&parent, target)?;
                if !parts.contains_key(&resolved) {
                    return Err(Error::Invalid(format!(
                        "Dangling relationship: {name} → {resolved}"
                    )));
                }
            }
        }
    }
    let mut recovered = Vec::new();
    for (name, info) in infos.iter().filter(|(n, _)| !n.ends_with(".rels")) {
        let rel_name = if let Some((dir, base)) = name.rsplit_once('/') {
            format!("{dir}/_rels/{base}.rels")
        } else {
            format!("_rels/{name}.rels")
        };
        for id in &info.references {
            if !infos
                .get(&rel_name)
                .is_some_and(|r| r.rels.iter().any(|(rid, _, _)| rid == id))
            {
                return Err(Error::Invalid(format!(
                    "Unresolved reference {id} in {name}"
                )));
            }
        }
        if name.starts_with("ppt/slides/") {
            recovered.extend(info.text.clone());
        }
    }
    let slides = infos
        .get("ppt/presentation.xml")
        .map_or(0, |x| x.slide_count);
    let slide_parts = parts
        .keys()
        .filter(|n| n.starts_with("ppt/slides/slide") && n.ends_with(".xml"))
        .count();
    if slides == 0 || slides != slide_parts || expected_slides.is_some_and(|v| v != slides) {
        return Err(Error::Invalid(format!(
            "Slide count mismatch: manifest {slides}, parts {slide_parts}, expected {expected_slides:?}"
        )));
    }
    for i in 1..=slides {
        if !parts.contains_key(&format!("ppt/slides/slide{i}.xml")) {
            return Err(Error::Invalid("Slide sequence is incomplete".into()));
        }
    }
    Ok(Validation{slides,parts:parts.len(),relationships:relationship_count,media:parts.keys().filter(|n|n.starts_with("ppt/media/")).count(),text:recovered,scope:"Archive integrity, balanced XML, slide count, internal relationships, referenced media and recoverable text. Viewer fidelity is not certified.".into()})
}
pub fn validate_file(path: &Path) -> Result<Validation> {
    let metadata = std::fs::metadata(path)?;
    if metadata.len() > 100 * 1024 * 1024 {
        return Err(Error::Invalid("PPTX exceeds size limit".into()));
    }
    validate_bytes(&std::fs::read(path)?, None)
}
