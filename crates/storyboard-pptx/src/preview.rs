//! SVG preview from resolved geometry. Native chart viewers can differ in label placement.
use crate::{Result, package, xml::escape};
use base64::{Engine, engine::general_purpose::STANDARD};
use std::path::Path;
use storyboard_core::{
    layout::{Element, LayoutDeck, Rect},
    model::{ChartKind, ShapeKind},
};
fn rect(r: Rect) -> String {
    format!(
        "x=\"{}\" y=\"{}\" width=\"{}\" height=\"{}\"",
        r.x, r.y, r.width, r.height
    )
}
fn label(x: f64, y: f64, s: &str, size: f64, color: &str) -> String {
    format!(
        "<text x=\"{x}\" y=\"{y}\" font-size=\"{size}\" fill=\"{color}\">{}</text>",
        escape(s)
    )
}
pub fn svg(deck: &LayoutDeck, index: usize, root: &Path) -> Result<String> {
    let slide = deck
        .slides
        .get(index)
        .ok_or_else(|| crate::Error::Invalid("Slide index is out of range".into()))?;
    let t = &deck.theme;
    let mut out = format!(
        "<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"960\" height=\"540\" viewBox=\"0 0 960 540\" role=\"img\" aria-label=\"{}\"><title>{}</title><rect width=\"960\" height=\"540\" fill=\"{}\"/><g font-family=\"{}, Calibri, sans-serif\">",
        escape(&slide.title),
        escape(&slide.title),
        slide.background,
        escape(&t.font)
    );
    for e in &slide.elements {
        match e {
            Element::Text {
                rect: r,
                text,
                size,
                color,
            } => {
                for (i, p) in text.paragraphs.iter().enumerate() {
                    let y = r.y + size * 0.84 + i as f64 * size * 1.22;
                    out.push_str(&format!("<text x=\"{}\" y=\"{y}\" font-size=\"{size}\" fill=\"#{color}\" xml:space=\"preserve\">",r.x));
                    if p.bullet {
                        out.push_str("<tspan>• </tspan>");
                    }
                    for run in &p.runs {
                        out.push_str(&format!(
                            "<tspan font-weight=\"{}\" font-style=\"{}\">{}</tspan>",
                            if run.bold { "700" } else { "400" },
                            if run.italic { "italic" } else { "normal" },
                            escape(&run.text)
                        ));
                    }
                    out.push_str("</text>");
                }
            }
            Element::Shape { rect: r, shape: s } => {
                let stroke = s.border.as_deref().unwrap_or("none");
                let stroke = if stroke == "none" {
                    stroke.into()
                } else {
                    format!("#{stroke}")
                };
                let color = format!(
                    "fill=\"#{}\" stroke=\"{stroke}\" stroke-width=\"{}\"",
                    s.fill, s.border_width
                );
                match s.kind{ShapeKind::Line=>out.push_str(&format!("<line x1=\"{}\" y1=\"{}\" x2=\"{}\" y2=\"{}\" stroke=\"#{stroke_color}\" stroke-width=\"{}\"/>",r.x,r.y,r.x+r.width,r.y+r.height,s.border_width,stroke_color=s.border.as_ref().unwrap_or(&s.fill))),ShapeKind::Ellipse=>out.push_str(&format!("<ellipse cx=\"{}\" cy=\"{}\" rx=\"{}\" ry=\"{}\" {color}/>",r.x+r.width/2.0,r.y+r.height/2.0,r.width/2.0,r.height/2.0)),_=>out.push_str(&format!("<rect {} rx=\"{}\" {color}/>",rect(*r),if s.kind==ShapeKind::RoundedRectangle{8}else{0}))}
            }
            Element::Image { rect: r, image } => {
                let asset = package::asset(root, image)?;
                let (actual, _) = package::image_geometry(*r, image, &asset);
                let data = STANDARD.encode(&asset.data);
                out.push_str(&format!("<svg {} viewBox=\"0 0 {} {}\" preserveAspectRatio=\"xMidYMid {}\"><image width=\"{}\" height=\"{}\" href=\"data:image/{};base64,{data}\"><title>{}</title></image></svg>",rect(actual),asset.width,asset.height,if image.fit==storyboard_core::ImageFit::Cover{"slice"}else{"meet"},asset.width,asset.height,asset.extension,escape(&image.alt)));
            }
            Element::Table {
                rect: r,
                table,
                size,
            } => {
                let w = r.width / table.columns.len() as f64;
                let h = r.height / (table.rows.len() + 1) as f64;
                for (i, row) in std::iter::once(&table.columns)
                    .chain(table.rows.iter())
                    .enumerate()
                {
                    for (j, value) in row.iter().enumerate() {
                        let cell = Rect {
                            x: r.x + j as f64 * w,
                            y: r.y + i as f64 * h,
                            width: w,
                            height: h,
                        };
                        out.push_str(&format!(
                            "<rect {} fill=\"#{}\" stroke=\"#{}\" stroke-width=\"0.5\"/>",
                            rect(cell),
                            if i == 0 { &t.surface } else { &t.background },
                            t.muted
                        ));
                        let mut text = storyboard_core::Text::plain(value);
                        text.paragraphs[0].runs[0].bold = i == 0;
                        let (text, size) = storyboard_core::layout::fitted(
                            &text,
                            Rect {
                                width: w - 16.0,
                                height: h - 12.0,
                                ..cell
                            },
                            *size,
                            12.0,
                        )?;
                        for (line, paragraph) in text.paragraphs.iter().enumerate() {
                            out.push_str(&format!("<text x=\"{}\" y=\"{}\" font-size=\"{size}\" font-weight=\"{}\" fill=\"#{}\">{}</text>",cell.x+8.0,cell.y+6.0+size*0.84+line as f64*size*1.22,if i==0{700}else{400},t.foreground,escape(&paragraph.runs.iter().map(|r|r.text.as_str()).collect::<String>())));
                        }
                    }
                }
            }
            Element::Chart { rect: r, chart } => {
                out.push_str(&label(
                    r.x,
                    r.y + 20.0,
                    &chart.title,
                    18.0,
                    &format!("#{}", t.foreground),
                ));
                let plot = Rect {
                    x: r.x + 40.0,
                    y: r.y + 42.0,
                    width: r.width - 60.0,
                    height: r.height - 80.0,
                };
                let max = chart
                    .series
                    .iter()
                    .flat_map(|s| &s.values)
                    .copied()
                    .fold(0.0, f64::max)
                    .max(1.0);
                let min = chart
                    .series
                    .iter()
                    .flat_map(|s| &s.values)
                    .copied()
                    .fold(0.0, f64::min);
                let range = max - min;
                let baseline = plot.y + plot.height * max / range;
                if chart.kind == ChartKind::Pie {
                    let values = &chart.series[0].values;
                    let sum: f64 = values.iter().sum();
                    let mut angle = -std::f64::consts::FRAC_PI_2;
                    let (cx, cy) = (plot.x + plot.width / 2.0, plot.y + plot.height / 2.0);
                    let radius = plot.height.min(plot.width) / 2.0;
                    for (i, value) in values.iter().enumerate() {
                        let span = if sum > 0.0 {
                            value / sum * std::f64::consts::TAU
                        } else {
                            0.0
                        };
                        let end = angle + span;
                        let (x1, y1) = (cx + radius * angle.cos(), cy + radius * angle.sin());
                        let (x2, y2) = (cx + radius * end.cos(), cy + radius * end.sin());
                        out.push_str(&format!("<path d=\"M {cx} {cy} L {x1} {y1} A {radius} {radius} 0 {} 1 {x2} {y2} Z\" fill=\"#{}\" stroke=\"#{}\"/>",u8::from(span>std::f64::consts::PI),if i%2==0{&t.accent}else{&t.muted},t.background));
                        angle = end;
                    }
                } else {
                    for (j, series) in chart.series.iter().enumerate() {
                        let color = if j % 2 == 0 { &t.accent } else { &t.muted };
                        let mut points = Vec::new();
                        for (i, value) in series.values.iter().enumerate() {
                            let group = plot.width / chart.categories.len() as f64;
                            let x = plot.x + i as f64 * group;
                            let y = plot.y + plot.height * (max - value) / range;
                            if chart.kind == ChartKind::Bar {
                                let w = group / (chart.series.len() + 1) as f64;
                                out.push_str(&format!("<rect x=\"{}\" y=\"{}\" width=\"{}\" height=\"{}\" fill=\"#{color}\"/>",x+j as f64*w,y.min(baseline),w*0.82,(y-baseline).abs()));
                            } else {
                                points.push(format!("{},{}", x + group / 2.0, y));
                            }
                        }
                        if chart.kind == ChartKind::Line {
                            out.push_str(&format!("<polyline points=\"{}\" fill=\"none\" stroke=\"#{color}\" stroke-width=\"3\"/>",points.join(" ")));
                        }
                    }
                    for (i, c) in chart.categories.iter().enumerate() {
                        out.push_str(&label(
                            plot.x + i as f64 * plot.width / chart.categories.len() as f64,
                            plot.y + plot.height + 18.0,
                            c,
                            12.0,
                            &format!("#{}", t.muted),
                        ));
                    }
                }
            }
        }
    }
    out.push_str("</g></svg>");
    Ok(out)
}
