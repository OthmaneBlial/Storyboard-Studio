//! Native editable PowerPoint output, independent of Python and external renderers.
mod chart;
mod package;
pub mod preview;
pub mod receipt;
pub mod validate;
mod xml;
use package::{Relationship, relationship};
use std::{collections::BTreeMap, path::Path};
use storyboard_core::{
    Story,
    layout::{Element, LayoutDeck},
    theme::Theme,
};

#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("{0}")]
    Core(#[from] storyboard_core::Error),
    #[error("File operation failed: {0}")]
    Io(#[from] std::io::Error),
    #[error("PPTX archive failed: {0}")]
    Zip(#[from] zip::result::ZipError),
    #[error("Invalid PPTX: {0}")]
    Invalid(String),
    #[error("JSON failed: {0}")]
    Json(#[from] serde_json::Error),
}
pub type Result<T> = std::result::Result<T, Error>;
pub struct Rendered {
    pub pptx: Vec<u8>,
    pub layout: LayoutDeck,
}
fn put(parts: &mut BTreeMap<String, Vec<u8>>, name: impl Into<String>, value: impl Into<String>) {
    parts.insert(name.into(), value.into().into_bytes());
}
fn picture(
    id: usize,
    rect: storyboard_core::Rect,
    image: &storyboard_core::Image,
    asset: &package::Asset,
    rid: &str,
) -> String {
    let (rect, crop) = package::image_geometry(rect, image, asset);
    format!(
        "<p:pic><p:nvPicPr><p:cNvPr id=\"{id}\" name=\"Image {id}\" descr=\"{}\"/><p:cNvPicPr><a:picLocks noChangeAspect=\"1\"/></p:cNvPicPr><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed=\"{rid}\"/>{crop}<a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr>{}<a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom></p:spPr></p:pic>",
        xml::escape(&image.alt),
        xml::xfrm(rect, "a")
    )
}
pub fn render(story: &Story, theme: &Theme, project_root: &Path) -> Result<Rendered> {
    let layout = storyboard_core::resolve(story, theme)?;
    let mut parts = BTreeMap::new();
    let mut media_count = 0;
    let mut chart_count = 0;
    let mut presentation_rels = vec![
        relationship("rId1", "slideMaster", "slideMasters/slideMaster1.xml"),
        relationship("rId2", "notesMaster", "notesMasters/notesMaster1.xml"),
    ];
    let mut slide_ids = String::new();
    for (i, s) in layout.slides.iter().enumerate() {
        let page = i + 1;
        slide_ids.push_str(&format!(
            "<p:sldId id=\"{}\" r:id=\"rId{}\"/>",
            256 + i,
            i + 3
        ));
        presentation_rels.push(relationship(
            format!("rId{}", i + 3),
            "slide",
            format!("slides/slide{page}.xml"),
        ));
        let mut rels = vec![
            relationship("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml"),
            relationship(
                "rId2",
                "notesSlide",
                format!("../notesSlides/notesSlide{page}.xml"),
            ),
        ];
        let mut shapes = String::new();
        for (j, element) in s.elements.iter().enumerate() {
            let id = j + 2;
            match element {
                Element::Text {
                    rect,
                    text,
                    size,
                    color,
                } => {
                    let mut links = Vec::new();
                    for run in text.paragraphs.iter().flat_map(|p| &p.runs) {
                        if let Some(url) = &run.hyperlink {
                            if !links.iter().any(|(u, _)| u == url) {
                                let rid = format!("rId{}", rels.len() + 1);
                                rels.push(Relationship {
                                    id: rid.clone(),
                                    kind: "hyperlink".into(),
                                    target: url.clone(),
                                    external: true,
                                });
                                links.push((url.clone(), rid));
                            }
                        }
                    }
                    shapes.push_str(&xml::text(
                        id,
                        *rect,
                        text,
                        *size,
                        color,
                        &theme.font,
                        &links,
                    ));
                }
                Element::Shape { rect, shape } => shapes.push_str(&xml::shape(id, *rect, shape)),
                Element::Table { rect, table, size } => {
                    shapes.push_str(&xml::table(id, *rect, table, *size, theme)?)
                }
                Element::Image { rect, image } => {
                    let asset = package::asset(project_root, image)?;
                    media_count += 1;
                    let media = format!("image{media_count}.{}", asset.extension);
                    let rid = format!("rId{}", rels.len() + 1);
                    shapes.push_str(&picture(id, *rect, image, &asset, &rid));
                    rels.push(relationship(rid, "image", format!("../media/{media}")));
                    parts.insert(format!("ppt/media/{media}"), asset.data);
                }
                Element::Chart { rect, chart } => {
                    chart_count += 1;
                    let rid = format!("rId{}", rels.len() + 1);
                    shapes.push_str(&format!("<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id=\"{id}\" name=\"Chart {id}\"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr>{}<a:graphic><a:graphicData uri=\"http://schemas.openxmlformats.org/drawingml/2006/chart\"><c:chart xmlns:c=\"http://schemas.openxmlformats.org/drawingml/2006/chart\" r:id=\"{rid}\"/></a:graphicData></a:graphic></p:graphicFrame>",xml::xfrm(*rect,"p")));
                    rels.push(relationship(
                        rid,
                        "chart",
                        format!("../charts/chart{chart_count}.xml"),
                    ));
                    put(
                        &mut parts,
                        format!("ppt/charts/chart{chart_count}.xml"),
                        chart::chart_xml(chart, theme),
                    );
                    put(
                        &mut parts,
                        format!("ppt/charts/_rels/chart{chart_count}.xml.rels"),
                        package::rels(&[relationship(
                            "rId1",
                            "package",
                            format!("../embeddings/chart{chart_count}.xlsx"),
                        )]),
                    );
                    parts.insert(
                        format!("ppt/embeddings/chart{chart_count}.xlsx"),
                        chart::workbook(chart)?,
                    );
                }
            }
        }
        put(
            &mut parts,
            format!("ppt/slides/slide{page}.xml"),
            format!(
                "{}<p:sld {}><p:cSld name=\"{}\"><p:bg><p:bgPr>{}<a:effectLst/></p:bgPr></p:bg><p:spTree>{}{shapes}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>",
                xml::HEADER,
                xml::NS,
                xml::escape(&s.title),
                xml::fill(&s.background),
                xml::GROUP
            ),
        );
        put(
            &mut parts,
            format!("ppt/slides/_rels/slide{page}.xml.rels"),
            package::rels(&rels),
        );
        let paragraphs = xml::paragraphs(
            &storyboard_core::Text::plain(&s.notes),
            12.0,
            &theme.foreground,
            &theme.font,
            &[],
        );
        put(
            &mut parts,
            format!("ppt/notesSlides/notesSlide{page}.xml"),
            format!(
                "{}<p:notes {}><p:cSld><p:spTree>{}<p:sp><p:nvSpPr><p:cNvPr id=\"2\" name=\"Speaker notes\"/><p:cNvSpPr/><p:nvPr><p:ph type=\"body\" idx=\"1\"/></p:nvPr></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/>{paragraphs}</p:txBody></p:sp></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:notes>",
                xml::HEADER,
                xml::NS,
                xml::GROUP
            ),
        );
        put(
            &mut parts,
            format!("ppt/notesSlides/_rels/notesSlide{page}.xml.rels"),
            package::rels(&[
                relationship("rId1", "notesMaster", "../notesMasters/notesMaster1.xml"),
                relationship("rId2", "slide", format!("../slides/slide{page}.xml")),
            ]),
        );
    }
    put(
        &mut parts,
        "ppt/presentation.xml",
        format!(
            "{}<p:presentation {}><p:sldMasterIdLst><p:sldMasterId id=\"2147483648\" r:id=\"rId1\"/></p:sldMasterIdLst><p:notesMasterIdLst><p:notesMasterId r:id=\"rId2\"/></p:notesMasterIdLst><p:sldIdLst>{slide_ids}</p:sldIdLst><p:sldSz cx=\"12192000\" cy=\"6858000\" type=\"screen16x9\"/><p:notesSz cx=\"6858000\" cy=\"9144000\"/><p:defaultTextStyle/></p:presentation>",
            xml::HEADER,
            xml::NS
        ),
    );
    put(
        &mut parts,
        "ppt/_rels/presentation.xml.rels",
        package::rels(&presentation_rels),
    );
    put(
        &mut parts,
        "ppt/slideMasters/slideMaster1.xml",
        format!(
            "{}<p:sldMaster {}><p:cSld><p:spTree>{}</p:spTree></p:cSld><p:clrMap {}/><p:sldLayoutIdLst><p:sldLayoutId id=\"2147483649\" r:id=\"rId1\"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>",
            xml::HEADER,
            xml::NS,
            xml::GROUP,
            xml::COLOR_MAP
        ),
    );
    put(
        &mut parts,
        "ppt/slideMasters/_rels/slideMaster1.xml.rels",
        package::rels(&[
            relationship("rId1", "slideLayout", "../slideLayouts/slideLayout1.xml"),
            relationship("rId2", "theme", "../theme/theme1.xml"),
        ]),
    );
    put(
        &mut parts,
        "ppt/slideLayouts/slideLayout1.xml",
        format!(
            "{}<p:sldLayout {} type=\"blank\" preserve=\"1\"><p:cSld name=\"Blank\"><p:spTree>{}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>",
            xml::HEADER,
            xml::NS,
            xml::GROUP
        ),
    );
    put(
        &mut parts,
        "ppt/slideLayouts/_rels/slideLayout1.xml.rels",
        package::rels(&[relationship(
            "rId1",
            "slideMaster",
            "../slideMasters/slideMaster1.xml",
        )]),
    );
    put(
        &mut parts,
        "ppt/notesMasters/notesMaster1.xml",
        format!(
            "{}<p:notesMaster {}><p:cSld><p:spTree>{}</p:spTree></p:cSld><p:clrMap {}/><p:notesStyle/></p:notesMaster>",
            xml::HEADER,
            xml::NS,
            xml::GROUP,
            xml::COLOR_MAP
        ),
    );
    put(
        &mut parts,
        "ppt/notesMasters/_rels/notesMaster1.xml.rels",
        package::rels(&[relationship("rId1", "theme", "../theme/theme1.xml")]),
    );
    put(&mut parts, "ppt/theme/theme1.xml", xml::theme(theme));
    put(
        &mut parts,
        "docProps/core.xml",
        format!(
            "{}<cp:coreProperties xmlns:cp=\"http://schemas.openxmlformats.org/package/2006/metadata/core-properties\" xmlns:dc=\"http://purl.org/dc/elements/1.1/\"><dc:title>{}</dc:title><dc:creator>{}</dc:creator><dc:description>{}</dc:description><cp:keywords>{}</cp:keywords></cp:coreProperties>",
            xml::HEADER,
            xml::escape(&story.presentation.title),
            xml::escape(&story.metadata.author),
            xml::escape(&story.metadata.description),
            xml::escape(&story.metadata.keywords.join(", "))
        ),
    );
    put(
        &mut parts,
        "docProps/app.xml",
        format!(
            "{}<Properties xmlns=\"http://schemas.openxmlformats.org/officeDocument/2006/extended-properties\"><Application>Storyboard Studio Rust</Application><PresentationFormat>Widescreen</PresentationFormat><Slides>{}</Slides><Notes>{}</Notes><AppVersion>03.0000</AppVersion></Properties>",
            xml::HEADER,
            layout.slides.len(),
            layout.slides.len()
        ),
    );
    put(
        &mut parts,
        "docProps/custom.xml",
        format!(
            "{}<Properties xmlns=\"http://schemas.openxmlformats.org/officeDocument/2006/custom-properties\" xmlns:vt=\"http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes\"><property fmtid=\"{{D5CDD505-2E9C-101B-9397-08002B2CF9AE}}\" pid=\"2\" name=\"StorySHA256\"><vt:lpwstr>{}</vt:lpwstr></property></Properties>",
            xml::HEADER,
            receipt::sha256(&serde_json::to_vec_pretty(story)?)
        ),
    );
    put(
        &mut parts,
        "_rels/.rels",
        package::rels(&[
            relationship("rId1", "officeDocument", "ppt/presentation.xml"),
            relationship(
                "rId2",
                "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties",
                "docProps/core.xml",
            ),
            relationship("rId3", "extended-properties", "docProps/app.xml"),
            relationship("rId4", "custom-properties", "docProps/custom.xml"),
        ]),
    );
    let mut overrides = String::new();
    for path in parts.keys() {
        let content = if path == "ppt/presentation.xml" {
            Some("presentationml.presentation.main")
        } else if path.starts_with("ppt/slides/") && !path.contains("/_rels/") {
            Some("presentationml.slide")
        } else if path.starts_with("ppt/slideMasters/") && !path.contains("/_rels/") {
            Some("presentationml.slideMaster")
        } else if path.starts_with("ppt/slideLayouts/") && !path.contains("/_rels/") {
            Some("presentationml.slideLayout")
        } else if path.starts_with("ppt/notesSlides/") && !path.contains("/_rels/") {
            Some("presentationml.notesSlide")
        } else if path.starts_with("ppt/notesMasters/") && !path.contains("/_rels/") {
            Some("presentationml.notesMaster")
        } else if path.starts_with("ppt/theme/") {
            Some("theme")
        } else if path.starts_with("ppt/charts/") && !path.contains("/_rels/") {
            Some("drawingml.chart")
        } else if path == "docProps/app.xml" {
            Some("extended-properties")
        } else if path == "docProps/custom.xml" {
            Some("custom-properties")
        } else {
            None
        };
        if let Some(kind) = content {
            overrides.push_str(&format!("<Override PartName=\"/{path}\" ContentType=\"application/vnd.openxmlformats-officedocument.{kind}+xml\"/>"));
        }
    }
    overrides.push_str("<Override PartName=\"/docProps/core.xml\" ContentType=\"application/vnd.openxmlformats-package.core-properties+xml\"/>");
    put(
        &mut parts,
        "[Content_Types].xml",
        format!(
            "{}<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\"><Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/><Default Extension=\"xml\" ContentType=\"application/xml\"/><Default Extension=\"png\" ContentType=\"image/png\"/><Default Extension=\"jpeg\" ContentType=\"image/jpeg\"/><Default Extension=\"xlsx\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet\"/>{overrides}</Types>",
            xml::HEADER
        ),
    );
    let pptx = package::zip(&parts)?;
    validate::validate_bytes(&pptx, Some(layout.slides.len()))?;
    Ok(Rendered { pptx, layout })
}
