use crate::{Error, FORMAT_VERSION, Result};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Story {
    #[schemars(schema_with = "version_schema")]
    pub schema_version: String,
    pub presentation: Presentation,
    #[serde(default)]
    pub audience: String,
    #[serde(default)]
    pub objective: String,
    #[serde(default)]
    pub owner: String,
    #[serde(default)]
    pub next_action: String,
    #[serde(default)]
    pub metadata: Metadata,
}
fn version_schema(_: &mut schemars::SchemaGenerator) -> schemars::Schema {
    schemars::json_schema!({"type": "string", "const": "3"})
}
#[derive(Debug, Clone, PartialEq, Default, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Metadata {
    #[serde(default)]
    pub author: String,
    #[serde(default)]
    pub description: String,
    #[serde(default)]
    pub synthetic: bool,
    #[serde(default)]
    pub keywords: Vec<String>,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Presentation {
    pub title: String,
    #[serde(default)]
    pub subtitle: String,
    #[serde(default = "default_theme")]
    pub theme: String,
    pub slides: Vec<Slide>,
}
fn default_theme() -> String {
    "midnight".into()
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Slide {
    pub id: String,
    pub title: String,
    #[serde(default)]
    pub purpose: String,
    #[serde(default)]
    pub role: Role,
    #[serde(default)]
    pub layout: Layout,
    #[serde(default)]
    pub blocks: Vec<Block>,
    #[serde(default)]
    pub claims: Vec<Claim>,
    #[serde(default)]
    pub evidence: Vec<Evidence>,
    #[serde(default)]
    pub notes: String,
    #[serde(default)]
    pub transition: String,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "kebab-case")]
pub enum Role {
    #[default]
    Context,
    Problem,
    Evidence,
    Options,
    Recommendation,
    Implications,
    Action,
    Appendix,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "kebab-case")]
pub enum Layout {
    #[default]
    Stack,
    Columns,
    Grid,
    Hero,
    Split,
    Sidebar,
    Absolute,
    Overlay,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(tag = "type", rename_all = "kebab-case", deny_unknown_fields)]
pub enum Block {
    Text {
        text: Text,
    },
    Heading {
        text: String,
    },
    Card {
        title: String,
        body: String,
    },
    Callout {
        title: String,
        body: String,
    },
    Quote {
        text: String,
        attribution: String,
    },
    Metric {
        value: String,
        label: String,
        context: String,
    },
    Image {
        image: Image,
    },
    Shape {
        shape: Shape,
    },
    Table {
        table: Table,
    },
    Chart {
        chart: Chart,
    },
    Group {
        layout: Layout,
        children: Vec<Block>,
    },
    Positioned {
        geometry: Geometry,
        block: Box<Block>,
    },
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Text {
    pub paragraphs: Vec<Paragraph>,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Paragraph {
    pub runs: Vec<TextRun>,
    #[serde(default)]
    pub bullet: bool,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct TextRun {
    pub text: String,
    #[serde(default)]
    pub bold: bool,
    #[serde(default)]
    pub italic: bool,
    #[serde(default)]
    pub hyperlink: Option<String>,
}
impl Text {
    pub fn plain(text: impl Into<String>) -> Self {
        Self {
            paragraphs: vec![Paragraph {
                runs: vec![TextRun {
                    text: text.into(),
                    bold: false,
                    italic: false,
                    hyperlink: None,
                }],
                bullet: false,
            }],
        }
    }
    pub fn content(&self) -> String {
        self.paragraphs
            .iter()
            .map(|p| p.runs.iter().map(|r| r.text.as_str()).collect::<String>())
            .collect::<Vec<_>>()
            .join("\n")
    }
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Image {
    pub path: String,
    pub alt: String,
    #[serde(default)]
    pub caption: String,
    #[serde(default)]
    pub fit: ImageFit,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "kebab-case")]
pub enum ImageFit {
    #[default]
    Contain,
    Cover,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Geometry {
    pub x: f64,
    pub y: f64,
    pub width: f64,
    pub height: f64,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Shape {
    pub kind: ShapeKind,
    pub fill: String,
    #[serde(default)]
    pub border: Option<String>,
    #[serde(default = "one")]
    pub border_width: f64,
}
fn one() -> f64 {
    1.0
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "kebab-case")]
pub enum ShapeKind {
    Rectangle,
    RoundedRectangle,
    Ellipse,
    Line,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Table {
    pub columns: Vec<String>,
    pub rows: Vec<Vec<String>>,
    #[serde(default)]
    pub summary: String,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Chart {
    pub title: String,
    pub categories: Vec<String>,
    pub series: Vec<ChartSeries>,
    #[serde(default)]
    pub kind: ChartKind,
    #[serde(default)]
    pub source_note: String,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "kebab-case")]
pub enum ChartKind {
    #[default]
    Bar,
    Line,
    Pie,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct ChartSeries {
    pub name: String,
    pub values: Vec<f64>,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Claim {
    pub id: String,
    pub text: String,
    #[serde(default)]
    pub assumption: bool,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Citation {
    pub label: String,
    #[serde(default)]
    pub locator: String,
    #[serde(default)]
    pub author: String,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Evidence {
    pub id: String,
    pub citation: Citation,
    pub kind: EvidenceKind,
    pub reference: String,
    #[serde(default)]
    pub excerpt: String,
    #[serde(default)]
    pub owner: String,
    #[serde(default)]
    pub claim_ids: Vec<String>,
    #[serde(default)]
    pub author_confirmed: bool,
    #[serde(default)]
    pub checked_date: Option<String>,
}
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize, JsonSchema)]
#[serde(rename_all = "kebab-case")]
pub enum EvidenceKind {
    Url,
    Document,
    LocalFile,
    Note,
    AuthorStatement,
}
impl Block {
    pub fn text(&self) -> String {
        match self {
            Self::Text { text } => text.content(),
            Self::Heading { text } => text.clone(),
            Self::Card { title, body } | Self::Callout { title, body } => {
                format!("{title}\n{body}")
            }
            Self::Quote { text, attribution } => format!("{text}\n{attribution}"),
            Self::Metric {
                value,
                label,
                context,
            } => format!("{value}\n{label}\n{context}"),
            Self::Image { image } => format!("{}\n{}", image.alt, image.caption),
            Self::Shape { .. } => String::new(),
            Self::Table { table } => table
                .columns
                .iter()
                .chain(table.rows.iter().flatten())
                .cloned()
                .collect::<Vec<_>>()
                .join("\n"),
            Self::Chart { chart } => format!(
                "{}\n{}\n{}",
                chart.title,
                chart.categories.join(" "),
                chart.source_note
            ),
            Self::Group { children, .. } => children
                .iter()
                .map(Self::text)
                .collect::<Vec<_>>()
                .join("\n"),
            Self::Positioned { block, .. } => block.text(),
        }
    }
}
pub fn valid_color(value: &str) -> bool {
    value.len() == 6 && value.bytes().all(|b| b.is_ascii_hexdigit())
}
pub fn valid_url(value: &str) -> bool {
    value.len() <= 4096
        && !value.chars().any(|c| c.is_control() || c.is_whitespace())
        && url::Url::parse(value).is_ok_and(|url| {
            matches!(url.scheme(), "https" | "http")
                && url.host_str().is_some()
                && url.username().is_empty()
                && url.password().is_none()
        })
}
fn valid_date(value: &str) -> bool {
    if value.len() != 10 || !value.is_ascii() || &value[4..5] != "-" || &value[7..8] != "-" {
        return false;
    }
    let (Ok(year), Ok(month), Ok(day)) = (
        value[..4].parse::<u32>(),
        value[5..7].parse::<u32>(),
        value[8..].parse::<u32>(),
    ) else {
        return false;
    };
    let max_day = match month {
        2 => {
            if year.is_multiple_of(4) && (!year.is_multiple_of(100) || year.is_multiple_of(400)) {
                29
            } else {
                28
            }
        }
        4 | 6 | 9 | 11 => 30,
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        _ => 0,
    };
    year > 0 && day >= 1 && day <= max_day
}
pub fn safe_relative_path(path: &str) -> bool {
    !path.is_empty()
        && !path.contains(['\\', ':'])
        && !std::path::Path::new(path).is_absolute()
        && std::path::Path::new(path)
            .components()
            .all(|c| matches!(c, std::path::Component::Normal(_)))
}
fn check_text(text: &str) -> Result<()> {
    if text.len() > 100_000
        || text
            .chars()
            .any(|c| c.is_control() && !matches!(c, '\n' | '\t' | '\r'))
    {
        return Err(Error::Invalid(
            "Text exceeds limits or contains XML control characters".into(),
        ));
    }
    Ok(())
}
fn validate_block(block: &Block, depth: usize) -> Result<()> {
    if depth > 8 {
        return Err(Error::Invalid("Block groups exceed depth 8".into()));
    }
    check_text(&block.text())?;
    match block {
        Block::Text { text } => {
            for run in text.paragraphs.iter().flat_map(|p| &p.runs) {
                if run.hyperlink.as_ref().is_some_and(|u| !valid_url(u)) {
                    return Err(Error::Invalid(
                        "Hyperlinks require safe HTTP(S) URLs".into(),
                    ));
                }
            }
        }
        Block::Image { image }
            if !safe_relative_path(&image.path) || image.alt.trim().is_empty() =>
        {
            return Err(Error::Invalid(
                "Images need a relative local path and alt text".into(),
            ));
        }
        Block::Shape { shape }
            if !valid_color(&shape.fill)
                || shape.border.as_ref().is_some_and(|c| !valid_color(c))
                || !shape.border_width.is_finite()
                || !(0.0..=20.0).contains(&shape.border_width) =>
        {
            return Err(Error::Invalid("Invalid shape color or stroke".into()));
        }
        Block::Table { table } => {
            check_text(&table.summary)?;
            if table.columns.is_empty()
                || table.columns.len() > 12
                || table.rows.len() > 30
                || table.rows.iter().any(|r| r.len() != table.columns.len())
            {
                return Err(Error::Invalid(
                    "Tables require 1–12 columns, ≤30 consistent rows".into(),
                ));
            }
        }
        Block::Chart { chart } => {
            for series in &chart.series {
                check_text(&series.name)?;
            }
            if chart.categories.is_empty()
                || chart.categories.len() > 50
                || chart.series.is_empty()
                || chart.series.len() > 8
                || chart.series.iter().any(|s| {
                    s.values.len() != chart.categories.len()
                        || s.values.iter().any(|v| !v.is_finite())
                })
                || (chart.kind == ChartKind::Pie
                    && (chart.series.len() != 1 || chart.series[0].values.iter().any(|v| *v < 0.0)))
            {
                return Err(Error::Invalid(
                    "Invalid chart dimensions or numeric values".into(),
                ));
            }
        }
        Block::Group { children, .. } => {
            if children.len() > 32 {
                return Err(Error::Invalid("Too many group children".into()));
            }
            for child in children {
                validate_block(child, depth + 1)?;
            }
        }
        Block::Positioned { geometry: g, block } => {
            if [g.x, g.y, g.width, g.height].iter().any(|v| !v.is_finite())
                || g.x < 0.0
                || g.y < 0.0
                || g.width <= 0.0
                || g.height <= 0.0
                || g.x + g.width > 960.0
                || g.y + g.height > 540.0
            {
                return Err(Error::Invalid(
                    "Absolute geometry must fit the 960×540 slide".into(),
                ));
            }
            validate_block(block, depth + 1)?;
        }
        _ => {}
    }
    Ok(())
}
impl Story {
    pub fn validate(&self) -> Result<()> {
        if self.schema_version != FORMAT_VERSION {
            return Err(Error::Invalid(format!(
                "Unsupported story version {}; expected {FORMAT_VERSION}. Use explicit migration for legacy stories.",
                self.schema_version
            )));
        }
        if self.presentation.title.trim().is_empty()
            || self.presentation.slides.is_empty()
            || self.presentation.slides.len() > 500
        {
            return Err(Error::Invalid(
                "A title and 1–500 slides are required".into(),
            ));
        }
        for text in [
            &self.presentation.title,
            &self.presentation.subtitle,
            &self.audience,
            &self.objective,
            &self.owner,
            &self.next_action,
            &self.metadata.author,
            &self.metadata.description,
        ] {
            check_text(text)?;
        }
        for keyword in &self.metadata.keywords {
            check_text(keyword)?;
        }
        let mut ids = BTreeSet::new();
        for slide in &self.presentation.slides {
            if slide.id.is_empty()
                || !ids.insert(&slide.id)
                || slide.title.trim().is_empty()
                || slide.blocks.len() > 32
            {
                return Err(Error::Invalid(
                    "Slides need unique nonempty IDs/titles and ≤32 blocks".into(),
                ));
            }
            for text in [
                &slide.title,
                &slide.purpose,
                &slide.notes,
                &slide.transition,
            ] {
                check_text(text)?;
            }
            for block in &slide.blocks {
                validate_block(block, 0)?;
            }
            let claims: BTreeSet<_> = slide.claims.iter().map(|c| &c.id).collect();
            if claims.len() != slide.claims.len() || claims.contains(&String::new()) {
                return Err(Error::Invalid("Claim IDs must be unique per slide".into()));
            }
            let mut evidence_ids = BTreeSet::new();
            for claim in &slide.claims {
                check_text(&claim.text)?;
            }
            for evidence in &slide.evidence {
                if evidence.id.is_empty()
                    || !evidence_ids.insert(&evidence.id)
                    || evidence.claim_ids.iter().any(|id| !claims.contains(id))
                {
                    return Err(Error::Invalid(
                        "Evidence IDs must be unique and claim links must resolve".into(),
                    ));
                }
                if evidence.kind == EvidenceKind::Url && !valid_url(&evidence.reference) {
                    return Err(Error::Invalid(
                        "Evidence URLs require HTTP(S) without credentials".into(),
                    ));
                }
                if evidence.kind == EvidenceKind::LocalFile
                    && !safe_relative_path(&evidence.reference)
                {
                    return Err(Error::Invalid(
                        "Local evidence path must stay in the project".into(),
                    ));
                }
                for text in [
                    &evidence.reference,
                    &evidence.excerpt,
                    &evidence.owner,
                    &evidence.citation.label,
                    &evidence.citation.locator,
                    &evidence.citation.author,
                ] {
                    check_text(text)?;
                }
                if evidence
                    .checked_date
                    .as_ref()
                    .is_some_and(|d| !valid_date(d))
                {
                    return Err(Error::Invalid(
                        "Evidence checked date must be a real YYYY-MM-DD date".into(),
                    ));
                }
                if evidence.author_confirmed
                    && (evidence.owner.trim().is_empty()
                        || evidence.excerpt.trim().is_empty()
                        || evidence
                            .checked_date
                            .as_ref()
                            .is_none_or(|d| d.trim().is_empty()))
                {
                    return Err(Error::Invalid(
                        "Author confirmation needs an owner, excerpt and checked date".into(),
                    ));
                }
            }
        }
        Ok(())
    }
}
