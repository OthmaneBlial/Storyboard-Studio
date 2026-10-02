//! Resolved slide geometry in points. 960 × 540 is a 16:9 presentation.
use crate::{Error, Result, model::*, theme::Theme};
use fontdue::{Font, FontSettings};
use serde::{Deserialize, Serialize};
use std::sync::OnceLock;

pub const WIDTH: f64 = 960.0;
pub const HEIGHT: f64 = 540.0;
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct Rect {
    pub x: f64,
    pub y: f64,
    pub width: f64,
    pub height: f64,
}
impl Rect {
    fn inset(self, v: f64) -> Self {
        Self {
            x: self.x + v,
            y: self.y + v,
            width: self.width - 2.0 * v,
            height: self.height - 2.0 * v,
        }
    }
    pub fn valid(self) -> bool {
        [self.x, self.y, self.width, self.height]
            .iter()
            .all(|x| x.is_finite())
            && self.x >= 0.0
            && self.y >= 0.0
            && self.width > 0.0
            && self.height > 0.0
            && self.x + self.width <= WIDTH + 0.01
            && self.y + self.height <= HEIGHT + 0.01
    }
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "kebab-case")]
pub enum Element {
    Text {
        rect: Rect,
        text: Text,
        size: f64,
        color: String,
    },
    Shape {
        rect: Rect,
        shape: Shape,
    },
    Image {
        rect: Rect,
        image: Image,
    },
    Table {
        rect: Rect,
        table: Table,
        size: f64,
    },
    Chart {
        rect: Rect,
        chart: Chart,
    },
}
impl Element {
    pub fn rect(&self) -> Rect {
        match self {
            Self::Text { rect, .. }
            | Self::Shape { rect, .. }
            | Self::Image { rect, .. }
            | Self::Table { rect, .. }
            | Self::Chart { rect, .. } => *rect,
        }
    }
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LayoutSlide {
    pub id: String,
    pub title: String,
    pub background: String,
    pub elements: Vec<Element>,
    pub notes: String,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct LayoutDeck {
    pub width: f64,
    pub height: f64,
    pub theme: Theme,
    pub slides: Vec<LayoutSlide>,
}
static REGULAR: OnceLock<std::result::Result<Font, String>> = OnceLock::new();
static BOLD: OnceLock<std::result::Result<Font, String>> = OnceLock::new();
fn font(bold: bool) -> Result<&'static Font> {
    let data: &[u8] = if bold {
        include_bytes!("../../../assets/fonts/Carlito-Bold.ttf")
    } else {
        include_bytes!("../../../assets/fonts/Carlito-Regular.ttf")
    };
    let cache = if bold { &BOLD } else { &REGULAR };
    cache
        .get_or_init(|| Font::from_bytes(data, FontSettings::default()).map_err(str::to_string))
        .as_ref()
        .map_err(|e| Error::Invalid(format!("Built-in font could not load: {e}")))
}
fn width(s: &str, size: f64, bold: bool) -> Result<f64> {
    Ok(s.chars()
        .map(|c| font(bold).map(|f| f.metrics(c, size as f32).advance_width as f64))
        .collect::<Result<Vec<_>>>()?
        .iter()
        .sum())
}
fn append(line: &mut Paragraph, run: &TextRun, value: String) {
    if let Some(last) = line.runs.last_mut() {
        if last.bold == run.bold && last.italic == run.italic && last.hyperlink == run.hyperlink {
            last.text.push_str(&value);
            return;
        }
    }
    let mut next = run.clone();
    next.text = value;
    line.runs.push(next);
}
/// Word wrapping retains styled runs and explicit paragraphs; long tokens break by glyph.
fn wrap(text: &Text, max_width: f64, size: f64) -> Result<Text> {
    let mut out = Vec::new();
    for paragraph in &text.paragraphs {
        let mut current = Paragraph {
            runs: Vec::new(),
            bullet: paragraph.bullet,
        };
        let mut used = if paragraph.bullet { size * 0.9 } else { 0.0 };
        for run in &paragraph.runs {
            for (i, logical_line) in run.text.split('\n').enumerate() {
                if i > 0 {
                    out.push(current);
                    current = Paragraph {
                        runs: Vec::new(),
                        bullet: false,
                    };
                    used = 0.0;
                }
                for word in logical_line.split_inclusive(char::is_whitespace) {
                    let w = width(word, size, run.bold)?;
                    if used + w > max_width && used > 0.0 {
                        out.push(current);
                        current = Paragraph {
                            runs: Vec::new(),
                            bullet: false,
                        };
                        used = 0.0;
                    }
                    if w > max_width {
                        for c in word.chars() {
                            let cw = width(&c.to_string(), size, run.bold)?;
                            if used + cw > max_width && used > 0.0 {
                                out.push(current);
                                current = Paragraph {
                                    runs: Vec::new(),
                                    bullet: false,
                                };
                                used = 0.0;
                            }
                            append(&mut current, run, c.to_string());
                            used += cw;
                        }
                    } else {
                        append(&mut current, run, word.into());
                        used += w;
                    }
                }
            }
        }
        out.push(current);
    }
    Ok(Text { paragraphs: out })
}
pub fn fitted(text: &Text, rect: Rect, max_size: f64, min_size: f64) -> Result<(Text, f64)> {
    let mut size = max_size;
    loop {
        let lines = wrap(text, rect.width, size)?;
        if lines.paragraphs.len() as f64 * size * 1.22 <= rect.height + 0.01 {
            return Ok((lines, size));
        }
        if size <= min_size {
            return Err(Error::Invalid(format!(
                "Text overflow: {} characters need more space than {:.0}×{:.0} points at minimum {min_size}pt",
                text.content().chars().count(),
                rect.width,
                rect.height
            )));
        }
        size = (size - 1.0).max(min_size);
    }
}
fn add_text(
    out: &mut Vec<Element>,
    rect: Rect,
    text: Text,
    size: f64,
    min: f64,
    color: &str,
) -> Result<()> {
    if text.content().is_empty() {
        return Ok(());
    }
    let (text, size) = fitted(&text, rect, size, min)?;
    out.push(Element::Text {
        rect,
        text,
        size,
        color: color.into(),
    });
    Ok(())
}
fn plain(
    out: &mut Vec<Element>,
    rect: Rect,
    value: &str,
    size: f64,
    min: f64,
    color: &str,
    bold: bool,
) -> Result<()> {
    let mut text = Text::plain(value);
    text.paragraphs[0].runs[0].bold = bold;
    add_text(out, rect, text, size, min, color)
}
fn regions(rect: Rect, count: usize, layout: Layout, gap: f64) -> Vec<Rect> {
    if count == 0 {
        return Vec::new();
    }
    let cols = match layout {
        Layout::Columns | Layout::Split => count,
        Layout::Grid => {
            if count > 4 {
                3
            } else {
                2
            }
        }
        Layout::Sidebar => 2,
        _ => 1,
    };
    let rows = count.div_ceil(cols);
    let w = (rect.width - gap * (cols - 1) as f64) / cols as f64;
    let h = (rect.height - gap * (rows - 1) as f64) / rows as f64;
    (0..count)
        .map(|i| Rect {
            x: rect.x + (i % cols) as f64 * (w + gap),
            y: rect.y + (i / cols) as f64 * (h + gap),
            width: w,
            height: h,
        })
        .collect()
}
fn place(block: &Block, rect: Rect, t: &Theme, out: &mut Vec<Element>) -> Result<()> {
    if !rect.valid() {
        return Err(Error::Invalid(
            "Layout contains invalid or out-of-bounds geometry".into(),
        ));
    }
    match block {
        Block::Text { text } => {
            add_text(out, rect, text.clone(), t.body_size, 12.0, &t.foreground)?
        }
        Block::Heading { text } => plain(
            out,
            rect,
            text,
            t.title_size * 0.75,
            18.0,
            &t.foreground,
            true,
        )?,
        Block::Card { title, body } | Block::Callout { title, body } => {
            let callout = matches!(block, Block::Callout { .. });
            out.push(Element::Shape {
                rect,
                shape: Shape {
                    kind: ShapeKind::RoundedRectangle,
                    fill: t.surface.clone(),
                    border: if callout {
                        Some(t.accent.clone())
                    } else {
                        None
                    },
                    border_width: 1.0,
                },
            });
            let inner = rect.inset(16.0);
            let title_h = if body.is_empty() {
                inner.height
            } else {
                (inner.height * 0.42).min(64.0)
            };
            plain(
                out,
                Rect {
                    height: title_h,
                    ..inner
                },
                title,
                t.body_size + 2.0,
                14.0,
                if callout { &t.accent } else { &t.foreground },
                true,
            )?;
            if !body.is_empty() {
                plain(
                    out,
                    Rect {
                        y: inner.y + title_h + 8.0,
                        height: inner.height - title_h - 8.0,
                        ..inner
                    },
                    body,
                    t.body_size,
                    12.0,
                    &t.foreground,
                    false,
                )?;
            }
        }
        Block::Quote { text, attribution } => {
            plain(
                out,
                Rect {
                    height: rect.height - 48.0,
                    ..rect
                },
                text,
                t.title_size * 0.85,
                18.0,
                &t.foreground,
                false,
            )?;
            plain(
                out,
                Rect {
                    y: rect.y + rect.height - 40.0,
                    height: 40.0,
                    ..rect
                },
                attribution,
                t.body_size,
                12.0,
                &t.muted,
                false,
            )?;
        }
        Block::Metric {
            value,
            label,
            context,
        } => {
            plain(
                out,
                Rect {
                    height: rect.height * 0.45,
                    ..rect
                },
                value,
                68.0,
                28.0,
                &t.accent,
                true,
            )?;
            plain(
                out,
                Rect {
                    y: rect.y + rect.height * 0.45,
                    height: rect.height * 0.25,
                    ..rect
                },
                label,
                t.body_size + 6.0,
                16.0,
                &t.foreground,
                true,
            )?;
            plain(
                out,
                Rect {
                    y: rect.y + rect.height * 0.7,
                    height: rect.height * 0.3,
                    ..rect
                },
                context,
                t.body_size,
                12.0,
                &t.muted,
                false,
            )?;
        }
        Block::Image { image } => out.push(Element::Image {
            rect,
            image: image.clone(),
        }),
        Block::Shape { shape } => out.push(Element::Shape {
            rect,
            shape: shape.clone(),
        }),
        Block::Table { table } => {
            let cell_w = rect.width / table.columns.len() as f64;
            let cell_h = rect.height / (table.rows.len() + 1) as f64;
            let mut size = t.body_size;
            for value in table.columns.iter().chain(table.rows.iter().flatten()) {
                let (_, fit) = fitted(
                    &Text::plain(value),
                    Rect {
                        width: cell_w - 16.0,
                        height: cell_h - 12.0,
                        ..rect
                    },
                    size,
                    12.0,
                )?;
                size = size.min(fit);
            }
            out.push(Element::Table {
                rect,
                table: table.clone(),
                size,
            });
        }
        Block::Chart { chart } => out.push(Element::Chart {
            rect,
            chart: chart.clone(),
        }),
        Block::Group { layout, children } => {
            for (child, r) in children
                .iter()
                .zip(regions(rect, children.len(), *layout, t.gap))
            {
                place(child, r, t, out)?;
            }
        }
        Block::Positioned { geometry: g, block } => place(
            block,
            Rect {
                x: g.x,
                y: g.y,
                width: g.width,
                height: g.height,
            },
            t,
            out,
        )?,
    }
    Ok(())
}
pub fn resolve(story: &Story, theme: &Theme) -> Result<LayoutDeck> {
    story.validate()?;
    theme.validate()?;
    // ponytail: built-in Carlito metrics; custom font loading/shaping is required before arbitrary font fidelity.
    if theme.font != "Carlito" {
        return Err(Error::Invalid("Measured native layouts currently require Carlito; install the bundled font for matching viewer rendering".into()));
    }
    let mut slides = Vec::new();
    for (i, s) in story.presentation.slides.iter().enumerate() {
        let run = || -> Result<LayoutSlide> {
            let mut elements = Vec::new();
            let m = theme.margin;
            plain(
                &mut elements,
                Rect {
                    x: m,
                    y: 24.0,
                    width: WIDTH - 2.0 * m,
                    height: 22.0,
                },
                &format!("{}  /  {:?}", story.presentation.title, s.role).to_uppercase(),
                11.0,
                9.0,
                &theme.muted,
                false,
            )?;
            plain(
                &mut elements,
                Rect {
                    x: m,
                    y: 60.0,
                    width: WIDTH - 2.0 * m,
                    height: 102.0,
                },
                &s.title,
                theme.title_size,
                24.0,
                &theme.foreground,
                true,
            )?;
            let content = Rect {
                x: m,
                y: 184.0,
                width: WIDTH - 2.0 * m,
                height: HEIGHT - 184.0 - m - 28.0,
            };
            let flow: Vec<_> = s
                .blocks
                .iter()
                .filter(|b| !matches!(b, Block::Positioned { .. }))
                .collect();
            let mode = if s.layout == Layout::Stack
                && flow.len() > 1
                && flow
                    .iter()
                    .all(|b| matches!(b, Block::Card { .. } | Block::Metric { .. }))
            {
                Layout::Grid
            } else {
                s.layout
            };
            for (block, r) in flow
                .iter()
                .zip(regions(content, flow.len(), mode, theme.gap))
            {
                place(block, r, theme, &mut elements)?;
            }
            for block in s
                .blocks
                .iter()
                .filter(|b| matches!(b, Block::Positioned { .. }))
            {
                place(block, content, theme, &mut elements)?;
            }
            elements.push(Element::Shape {
                rect: Rect {
                    x: m,
                    y: HEIGHT - 38.0,
                    width: WIDTH - 2.0 * m,
                    height: 0.5,
                },
                shape: Shape {
                    kind: ShapeKind::Line,
                    fill: theme.muted.clone(),
                    border: Some(theme.muted.clone()),
                    border_width: 0.5,
                },
            });
            let label = if story.metadata.synthetic {
                "SYNTHETIC EXAMPLE  ·  STORYBOARD STUDIO"
            } else {
                "STORYBOARD STUDIO"
            };
            plain(
                &mut elements,
                Rect {
                    x: m,
                    y: HEIGHT - 28.0,
                    width: WIDTH - 2.0 * m - 60.0,
                    height: 20.0,
                },
                label,
                10.0,
                9.0,
                &theme.muted,
                false,
            )?;
            plain(
                &mut elements,
                Rect {
                    x: WIDTH - m - 45.0,
                    y: HEIGHT - 28.0,
                    width: 45.0,
                    height: 20.0,
                },
                &format!("{:02}", i + 1),
                10.0,
                9.0,
                &theme.muted,
                false,
            )?;
            let mut notes = s.notes.clone();
            for e in &s.evidence {
                notes.push_str(&format!(
                    "\nSource: {} · {} · {} · author-confirmed: {}",
                    e.citation.label, e.reference, e.excerpt, e.author_confirmed
                ));
            }
            Ok(LayoutSlide {
                id: s.id.clone(),
                title: s.title.clone(),
                background: theme.background.clone(),
                elements,
                notes,
            })
        };
        slides.push(run().map_err(|e| Error::Layout {
            slide: i + 1,
            message: e.to_string(),
        })?);
    }
    Ok(LayoutDeck {
        width: WIDTH,
        height: HEIGHT,
        theme: theme.clone(),
        slides,
    })
}
