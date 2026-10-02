use storyboard_core::*;
const EXAMPLE: &str = include_str!("../../../examples/startup-pitch.md");
#[test]
fn markdown_retains_authored_structure_and_metadata() {
    let story = compile(EXAMPLE, true).unwrap();
    assert_eq!(story.presentation.slides.len(), 7);
    assert_eq!(story.owner, "Maya, product lead");
    assert!(story.metadata.synthetic);
    assert_eq!(story.presentation.slides[1].blocks.len(), 3);
    assert!(
        story.presentation.slides[0]
            .notes
            .contains("Entirely synthetic")
    );
    assert_eq!(story.presentation.slides.last().unwrap().role, Role::Action);
    assert_eq!(
        compile(&serde_json::to_string(&story).unwrap(), false).unwrap(),
        story
    );
}
#[test]
fn legacy_decision_brief_compiles_without_inventing_evidence() {
    let story = compile(
        include_str!("../../../examples/briefs/onboarding-decision.json"),
        false,
    )
    .unwrap();
    assert_eq!(story.presentation.slides.len(), 7);
    assert!(
        story
            .presentation
            .slides
            .iter()
            .flat_map(|s| &s.blocks)
            .any(|b| b.text().contains("Concierge pilot"))
    );
    let evidence: Vec<_> = story
        .presentation
        .slides
        .iter()
        .flat_map(|s| &s.evidence)
        .collect();
    assert_eq!(evidence.len(), 1);
    assert!(!evidence[0].author_confirmed);
    assert_eq!(diagnose(&story).author_confirmed_claims, 0);
}
#[test]
fn rejects_unknown_versions_fields_and_empty_inputs() {
    let story = compile(EXAMPLE, true).unwrap();
    let mut v = serde_json::to_value(&story).unwrap();
    v["schema_version"] = "4".into();
    assert!(compile(&v.to_string(), false).is_err());
    v["schema_version"] = "3".into();
    v["silent_extra"] = true.into();
    assert!(compile(&v.to_string(), false).is_err());
    assert!(compile("", true).is_err());
    assert!(compile("# Title\n### Orphan\nbody", true).is_err());
}
#[test]
fn rejects_invalid_claim_links_and_url_credentials() {
    let mut s = compile(EXAMPLE, true).unwrap();
    s.presentation.slides[0].evidence.push(Evidence {
        id: "e1".into(),
        citation: Citation {
            label: "Source".into(),
            locator: String::new(),
            author: String::new(),
        },
        kind: EvidenceKind::Url,
        reference: "https://user:password@example.com".into(),
        excerpt: "excerpt".into(),
        owner: "author".into(),
        claim_ids: vec!["missing".into()],
        author_confirmed: false,
        checked_date: None,
    });
    assert!(s.validate().is_err());
    s.presentation.slides[0].evidence[0].claim_ids.clear();
    assert!(s.validate().is_err());
    s.presentation.slides[0].evidence[0].reference = "https://example.com".into();
    s.presentation.slides[0].evidence[0].author_confirmed = true;
    assert!(s.validate().is_err());
}
#[test]
fn layout_is_deterministic_in_bounds_and_does_not_drop_copy() {
    let s = compile(EXAMPLE, true).unwrap();
    for t in themes() {
        t.validate().unwrap();
        let a = resolve(&s, &t).unwrap();
        assert_eq!(a, resolve(&s, &t).unwrap());
        for slide in &a.slides {
            assert!(slide.elements.iter().all(|e| e.rect().valid()));
        }
        let extracted = a
            .slides
            .iter()
            .flat_map(|s| &s.elements)
            .filter_map(|e| {
                if let Element::Text { text, .. } = e {
                    Some(text.content())
                } else {
                    None
                }
            })
            .collect::<Vec<_>>()
            .join(" ");
        assert!(
            extracted
                .split_whitespace()
                .collect::<Vec<_>>()
                .join(" ")
                .contains("manual linking")
        );
    }
}
#[test]
fn overflowing_content_is_an_error() {
    let mut s = compile(EXAMPLE, true).unwrap();
    s.presentation.slides[0].blocks = vec![Block::Text {
        text: Text::plain("overflow ".repeat(5000)),
    }];
    assert!(
        resolve(&s, &Theme::named("midnight").unwrap())
            .unwrap_err()
            .to_string()
            .contains("overflow")
    );
}
#[test]
fn doctor_reports_specific_missing_claim_owner_action_and_duplicates() {
    let mut s = compile(EXAMPLE, true).unwrap();
    s.owner.clear();
    s.next_action.clear();
    let mut slide = s.presentation.slides[0].clone();
    slide.id = "duplicate".into();
    s.presentation.slides.push(slide);
    s.presentation.slides[0].claims.push(Claim {
        id: "c1".into(),
        text: "Unsubstantiated claim".into(),
        assumption: false,
    });
    let r = diagnose(&s);
    for code in [
        "owner.missing",
        "action.missing",
        "slide.duplicate",
        "claim.unsupported",
    ] {
        assert!(r.findings.iter().any(|f| f.code == code), "{code}");
    }
    assert_eq!(r.claims, 1);
    assert_eq!(r.author_confirmed_claims, 0);
    assert!(r.markdown().contains("factual truth"));
}
#[test]
fn unsafe_assets_geometry_and_malformed_tables_are_rejected() {
    let mut s = compile(EXAMPLE, true).unwrap();
    for path in [
        "../secret.png",
        "/etc/passwd",
        "C:\\secret.png",
        "https://example.com/image.png",
    ] {
        s.presentation.slides[0].blocks = vec![Block::Image {
            image: Image {
                path: path.into(),
                alt: "image".into(),
                caption: String::new(),
                fit: ImageFit::Contain,
            },
        }];
        assert!(s.validate().is_err());
    }
    s.presentation.slides[0].blocks = vec![Block::Table {
        table: Table {
            columns: vec!["a".into()],
            rows: vec![vec!["b".into(), "c".into()]],
            summary: String::new(),
        },
    }];
    assert!(s.validate().is_err());
}
