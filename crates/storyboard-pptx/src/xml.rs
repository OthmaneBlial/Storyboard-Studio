use storyboard_core::{layout::Rect, model::*, theme::Theme};

pub const HEADER: &str = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>";
pub const NS: &str = "xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\" xmlns:p=\"http://schemas.openxmlformats.org/presentationml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\"";
pub const GROUP: &str = "<p:nvGrpSpPr><p:cNvPr id=\"1\" name=\"\"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x=\"0\" y=\"0\"/><a:ext cx=\"0\" cy=\"0\"/><a:chOff x=\"0\" y=\"0\"/><a:chExt cx=\"0\" cy=\"0\"/></a:xfrm></p:grpSpPr>";
pub const COLOR_MAP: &str = "accent1=\"accent1\" accent2=\"accent2\" accent3=\"accent3\" accent4=\"accent4\" accent5=\"accent5\" accent6=\"accent6\" bg1=\"lt1\" bg2=\"lt2\" folHlink=\"folHlink\" hlink=\"hlink\" tx1=\"dk1\" tx2=\"dk2\"";
pub fn escape(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&apos;")
}
pub fn emu(pt: f64) -> i64 {
    (pt * 12700.0).round() as i64
}
pub fn xfrm(r: Rect, prefix: &str) -> String {
    format!(
        "<{prefix}:xfrm><a:off x=\"{}\" y=\"{}\"/><a:ext cx=\"{}\" cy=\"{}\"/></{prefix}:xfrm>",
        emu(r.x),
        emu(r.y),
        emu(r.width),
        emu(r.height)
    )
}
pub fn fill(color: &str) -> String {
    format!(
        "<a:solidFill><a:srgbClr val=\"{}\"/></a:solidFill>",
        escape(color)
    )
}
pub fn paragraphs(
    text: &Text,
    size: f64,
    color: &str,
    font: &str,
    links: &[(String, String)],
) -> String {
    let mut out = String::new();
    for p in &text.paragraphs {
        let bullet = if p.bullet {
            "<a:buChar char=\"•\"/>"
        } else {
            "<a:buNone/>"
        };
        out.push_str(&format!(
            "<a:p><a:pPr><a:lnSpc><a:spcPts val=\"{}\"/></a:lnSpc>{bullet}</a:pPr>",
            (size * 122.0).round() as i64
        ));
        for run in &p.runs {
            let link = run
                .hyperlink
                .as_ref()
                .and_then(|url| links.iter().find(|(u, _)| u == url))
                .map(|(_, id)| format!("<a:hlinkClick r:id=\"{id}\"/>"))
                .unwrap_or_default();
            out.push_str(&format!("<a:r><a:rPr lang=\"en-US\" sz=\"{}\" b=\"{}\" i=\"{}\">{}<a:latin typeface=\"{}\"/>{link}</a:rPr><a:t xml:space=\"preserve\">{}</a:t></a:r>",(size*100.0).round()as i64,u8::from(run.bold),u8::from(run.italic),fill(color),escape(font),escape(&run.text)));
        }
        out.push_str(&format!(
            "<a:endParaRPr lang=\"en-US\" sz=\"{}\"/></a:p>",
            (size * 100.0).round() as i64
        ));
    }
    out
}
pub fn text(
    id: usize,
    r: Rect,
    text: &Text,
    size: f64,
    color: &str,
    font: &str,
    links: &[(String, String)],
) -> String {
    format!(
        "<p:sp><p:nvSpPr><p:cNvPr id=\"{id}\" name=\"Text {id}\"/><p:cNvSpPr txBox=\"1\"/><p:nvPr/></p:nvSpPr><p:spPr>{}<a:prstGeom prst=\"rect\"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap=\"none\" lIns=\"0\" tIns=\"0\" rIns=\"0\" bIns=\"0\" anchor=\"t\"><a:noAutofit/></a:bodyPr><a:lstStyle/>{}</p:txBody></p:sp>",
        xfrm(r, "a"),
        paragraphs(text, size, color, font, links)
    )
}
pub fn shape(id: usize, r: Rect, s: &Shape) -> String {
    let geom = match s.kind {
        ShapeKind::Rectangle => "rect",
        ShapeKind::RoundedRectangle => "roundRect",
        ShapeKind::Ellipse => "ellipse",
        ShapeKind::Line => "line",
    };
    let background = if s.kind == ShapeKind::Line {
        "<a:noFill/>".into()
    } else {
        fill(&s.fill)
    };
    let stroke = s
        .border
        .as_ref()
        .map(|color| {
            format!(
                "<a:ln w=\"{}\">{}<a:prstDash val=\"solid\"/></a:ln>",
                emu(s.border_width),
                fill(color)
            )
        })
        .unwrap_or_else(|| "<a:ln><a:noFill/></a:ln>".into());
    format!(
        "<p:sp><p:nvSpPr><p:cNvPr id=\"{id}\" name=\"Shape {id}\"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>{}<a:prstGeom prst=\"{geom}\"><a:avLst/></a:prstGeom>{background}{stroke}</p:spPr></p:sp>",
        xfrm(r, "a")
    )
}
pub fn table(id: usize, r: Rect, t: &Table, size: f64, theme: &Theme) -> crate::Result<String> {
    let grid = (0..t.columns.len())
        .map(|_| {
            format!(
                "<a:gridCol w=\"{}\"/>",
                emu(r.width / t.columns.len() as f64)
            )
        })
        .collect::<String>();
    let mut rows = String::new();
    for (i, row) in std::iter::once(&t.columns).chain(t.rows.iter()).enumerate() {
        rows.push_str(&format!(
            "<a:tr h=\"{}\">",
            emu(r.height / (t.rows.len() + 1) as f64)
        ));
        for value in row {
            let mut value = Text::plain(value);
            value.paragraphs[0].runs[0].bold = i == 0;
            let (value, size) = storyboard_core::layout::fitted(
                &value,
                Rect {
                    width: r.width / t.columns.len() as f64 - 16.0,
                    height: r.height / (t.rows.len() + 1) as f64 - 12.0,
                    ..r
                },
                size,
                12.0,
            )?;
            rows.push_str(&format!("<a:tc><a:txBody><a:bodyPr wrap=\"none\" lIns=\"0\" tIns=\"0\" rIns=\"0\" bIns=\"0\"/><a:lstStyle/>{}</a:txBody><a:tcPr marL=\"101600\" marR=\"101600\" marT=\"76200\" marB=\"76200\">{}</a:tcPr></a:tc>",paragraphs(&value,size,&theme.foreground,&theme.font,&[]),fill(if i==0{&theme.surface}else{&theme.background})));
        }
        rows.push_str("</a:tr>");
    }
    Ok(format!(
        "<p:graphicFrame><p:nvGraphicFramePr><p:cNvPr id=\"{id}\" name=\"Table {id}\" descr=\"{}\"/><p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr>{}<a:graphic><a:graphicData uri=\"http://schemas.openxmlformats.org/drawingml/2006/table\"><a:tbl><a:tblPr firstRow=\"1\" bandRow=\"1\"/><a:tblGrid>{grid}</a:tblGrid>{rows}</a:tbl></a:graphicData></a:graphic></p:graphicFrame>",
        escape(&t.summary),
        xfrm(r, "p")
    ))
}
pub fn theme(t: &Theme) -> String {
    let colors = [
        ("dk1", &t.foreground),
        ("lt1", &t.background),
        ("dk2", &t.muted),
        ("lt2", &t.surface),
        ("accent1", &t.accent),
        ("accent2", &t.muted),
        ("accent3", &t.accent),
        ("accent4", &t.foreground),
        ("accent5", &t.muted),
        ("accent6", &t.accent),
        ("hlink", &t.accent),
        ("folHlink", &t.muted),
    ]
    .into_iter()
    .map(|(name, color)| format!("<a:{name}><a:srgbClr val=\"{color}\"/></a:{name}>"))
    .collect::<String>();
    let font = escape(&t.font);
    let fonts=["majorFont","minorFont"].into_iter().map(|name|format!("<a:{name}><a:latin typeface=\"{font}\"/><a:ea typeface=\"\"/><a:cs typeface=\"\"/></a:{name}>")).collect::<String>();
    let solid = "<a:solidFill><a:schemeClr val=\"phClr\"/></a:solidFill>";
    let lines = (1..=3)
        .map(|i| {
            format!(
                "<a:ln w=\"{}\">{solid}<a:prstDash val=\"solid\"/></a:ln>",
                i * 12700
            )
        })
        .collect::<String>();
    format!(
        "{HEADER}<a:theme xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\" name=\"{}\"><a:themeElements><a:clrScheme name=\"Storyboard\">{colors}</a:clrScheme><a:fontScheme name=\"Storyboard\">{fonts}</a:fontScheme><a:fmtScheme name=\"Storyboard\"><a:fillStyleLst>{}</a:fillStyleLst><a:lnStyleLst>{lines}</a:lnStyleLst><a:effectStyleLst>{}</a:effectStyleLst><a:bgFillStyleLst>{}</a:bgFillStyleLst></a:fmtScheme></a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/></a:theme>",
        escape(&t.name),
        solid.repeat(3),
        "<a:effectStyle><a:effectLst/></a:effectStyle>".repeat(3),
        solid.repeat(3)
    )
}
