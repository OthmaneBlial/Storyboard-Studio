use std::{
    collections::BTreeMap,
    io::{Cursor, Read, Write},
    path::Path,
};
use storyboard_core::*;
use storyboard_pptx::{preview, receipt, render, validate};
const EXAMPLE: &str = include_str!("../../../examples/startup-pitch.md");
fn entries(bytes: &[u8]) -> BTreeMap<String, Vec<u8>> {
    let mut z = zip::ZipArchive::new(Cursor::new(bytes)).unwrap();
    (0..z.len())
        .map(|i| {
            let mut f = z.by_index(i).unwrap();
            let name = f.name().to_string();
            let mut data = Vec::new();
            f.read_to_end(&mut data).unwrap();
            (name, data)
        })
        .collect()
}
fn archive(parts: &BTreeMap<String, Vec<u8>>) -> Vec<u8> {
    let mut z = zip::ZipWriter::new(Cursor::new(Vec::new()));
    for (n, data) in parts {
        z.start_file(n, zip::write::SimpleFileOptions::default())
            .unwrap();
        z.write_all(data).unwrap();
    }
    z.finish().unwrap().into_inner()
}
#[test]
fn package_is_deterministic_editable_and_recovers_unicode() {
    let mut s = compile(EXAMPLE, true).unwrap();
    s.presentation.slides[0].title = "Café <tests> & editable text".into();
    let t = Theme::named("midnight").unwrap();
    let a = render(&s, &t, Path::new(".")).unwrap();
    assert_eq!(a.pptx, render(&s, &t, Path::new(".")).unwrap().pptx);
    let r = validate::validate_bytes(&a.pptx, Some(7)).unwrap();
    assert!(r.text.join(" ").contains("Café <tests> & editable text"));
    let p = entries(&a.pptx);
    assert!(p.contains_key("ppt/notesSlides/notesSlide1.xml"));
    assert!(
        String::from_utf8(p["ppt/slides/slide1.xml"].clone())
            .unwrap()
            .contains("<p:txBody>")
    );
    assert!(!p.keys().any(|n| n.starts_with("ppt/media/")));
}
#[test]
fn dangling_relationships_missing_parts_malformed_xml_and_counts_fail() {
    let s = compile(EXAMPLE, true).unwrap();
    let a = render(&s, &Theme::named("midnight").unwrap(), Path::new(".")).unwrap();
    let mut p = entries(&a.pptx);
    p.remove("ppt/theme/theme1.xml");
    assert!(validate::validate_bytes(&archive(&p), Some(7)).is_err());
    let mut p = entries(&a.pptx);
    p.insert(
        "ppt/slides/slide1.xml".into(),
        b"<broken><unclosed></broken>".to_vec(),
    );
    assert!(validate::validate_bytes(&archive(&p), None).is_err());
    assert!(validate::validate_bytes(&a.pptx, Some(8)).is_err());
    let mut p = entries(&a.pptx);
    p.insert("../escape.xml".into(), b"<x/>".to_vec());
    assert!(validate::validate_bytes(&archive(&p), None).is_err());
    let mut p = entries(&a.pptx);
    p.insert(
        "ppt/slides/slide1.xml".into(),
        b"<!DOCTYPE x SYSTEM 'file:///etc/passwd'><x/>".to_vec(),
    );
    assert!(validate::validate_bytes(&archive(&p), None).is_err());
}
#[test]
fn receipts_detect_tampering_and_prevent_accidental_overwrite() {
    let dir = tempfile::tempdir().unwrap();
    let path = dir.path().join("deck.pptx");
    let story = compile(EXAMPLE, true).unwrap();
    let a = render(&story, &Theme::named("midnight").unwrap(), dir.path()).unwrap();
    receipt::save_bundle(&story, &a, &path, false).unwrap();
    receipt::verify(&path.with_extension("receipt.json")).unwrap();
    assert!(receipt::save_bundle(&story, &a, &path, false).is_err());
    let receipt_path = path.with_extension("receipt.json");
    let mut r: receipt::Receipt =
        serde_json::from_slice(&std::fs::read(&receipt_path).unwrap()).unwrap();
    r.diagnostics.claims = 1000;
    std::fs::write(&receipt_path, serde_json::to_vec(&r).unwrap()).unwrap();
    assert!(receipt::verify(&receipt_path).is_err());
    receipt::save_bundle(&story, &a, &path, true).unwrap();
    std::fs::write(&path, b"tampered").unwrap();
    assert!(receipt::verify(&receipt_path).is_err());
}
#[test]
fn native_tables_charts_images_links_and_notes_resolve() {
    let dir = tempfile::tempdir().unwrap();
    let img = image::RgbImage::from_pixel(80, 40, image::Rgb([20, 90, 100]));
    img.save(dir.path().join("image.png")).unwrap();
    let mut story = compile(EXAMPLE, true).unwrap();
    story.presentation.slides.truncate(4);
    let slide = &mut story.presentation.slides[0];
    slide.blocks = vec![Block::Image {
        image: Image {
            path: "image.png".into(),
            alt: "Synthetic wide image".into(),
            caption: String::new(),
            fit: ImageFit::Contain,
        },
    }];
    story.presentation.slides[1].blocks = vec![Block::Table {
        table: Table {
            columns: vec!["Option".into(), "Cost".into()],
            rows: vec![vec!["A".into(), "20".into()], vec!["B".into(), "40".into()]],
            summary: "Synthetic costs".into(),
        },
    }];
    story.presentation.slides[2].blocks = vec![Block::Chart {
        chart: Chart {
            title: "Synthetic pilot".into(),
            categories: vec!["A".into(), "B".into()],
            series: vec![ChartSeries {
                name: "Cost".into(),
                values: vec![20.0, 40.0],
            }],
            kind: ChartKind::Bar,
            source_note: "Synthetic data".into(),
        },
    }];
    let mut text = Text::plain("Evidence link");
    text.paragraphs[0].runs[0].hyperlink = Some("https://example.com/source?a=1&b=2".into());
    text.paragraphs[0].runs[0].bold = true;
    story.presentation.slides[3].blocks = vec![Block::Text { text }];
    story.presentation.slides[3].notes = "Notes café & review".into();
    let a = render(&story, &Theme::named("minimal").unwrap(), dir.path()).unwrap();
    let r = validate::validate_bytes(&a.pptx, Some(4)).unwrap();
    assert_eq!(r.media, 1);
    let p = entries(&a.pptx);
    assert!(p.contains_key("ppt/charts/chart1.xml"));
    assert!(p.contains_key("ppt/embeddings/chart1.xlsx"));
    let workbook = entries(&p["ppt/embeddings/chart1.xlsx"]);
    assert!(
        String::from_utf8(workbook["xl/worksheets/sheet1.xml"].clone())
            .unwrap()
            .contains("40")
    );
    assert!(
        String::from_utf8(p["ppt/slides/slide2.xml"].clone())
            .unwrap()
            .contains("<a:tbl>")
    );
    assert!(
        String::from_utf8(p["ppt/slides/slide4.xml"].clone())
            .unwrap()
            .contains("<a:hlinkClick")
    );
    assert!(
        String::from_utf8(p["ppt/notesSlides/notesSlide4.xml"].clone())
            .unwrap()
            .contains("Notes café &amp; review")
    );
    assert!(
        preview::svg(&a.layout, 0, dir.path())
            .unwrap()
            .contains("data:image/png;base64,")
    );
}
#[cfg(unix)]
#[test]
fn image_and_receipt_symlinks_cannot_escape_project() {
    let root = tempfile::tempdir().unwrap();
    let other = tempfile::tempdir().unwrap();
    std::fs::write(other.path().join("secret.png"), b"not an image").unwrap();
    std::os::unix::fs::symlink(
        other.path().join("secret.png"),
        root.path().join("escape.png"),
    )
    .unwrap();
    let mut s = compile(EXAMPLE, true).unwrap();
    s.presentation.slides[0].blocks = vec![Block::Image {
        image: Image {
            path: "escape.png".into(),
            alt: "bad".into(),
            caption: String::new(),
            fit: ImageFit::Contain,
        },
    }];
    assert!(render(&s, &Theme::named("midnight").unwrap(), root.path()).is_err());
}

#[test]
fn preview_background_uses_the_resolved_theme_color() {
    let story =
        storyboard_core::compile(include_str!("../../../examples/startup-pitch.md"), true).unwrap();
    let theme = storyboard_core::Theme::named("consulting").unwrap();
    let layout = storyboard_core::resolve(&story, &theme).unwrap();
    let svg = storyboard_pptx::preview::svg(&layout, 0, std::path::Path::new(".")).unwrap();
    assert!(svg.contains(&format!("height=\"540\" fill=\"#{}\"", theme.background)));
}
