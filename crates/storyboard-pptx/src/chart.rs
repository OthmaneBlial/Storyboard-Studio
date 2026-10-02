use crate::{
    Result,
    package::{self, relationship},
    xml::{self, escape},
};
use std::collections::BTreeMap;
use storyboard_core::{
    model::{Chart, ChartKind},
    theme::Theme,
};
fn column(index: usize) -> String {
    let mut n = index + 1;
    let mut name = String::new();
    while n > 0 {
        n -= 1;
        name.insert(0, (b'A' + (n % 26) as u8) as char);
        n /= 26;
    }
    name
}
fn strings(values: &[String]) -> String {
    format!(
        "<c:strCache><c:ptCount val=\"{}\"/>{}</c:strCache>",
        values.len(),
        values
            .iter()
            .enumerate()
            .map(|(i, v)| format!("<c:pt idx=\"{i}\"><c:v>{}</c:v></c:pt>", escape(v)))
            .collect::<String>()
    )
}
pub fn chart_xml(chart: &Chart, t: &Theme) -> String {
    let mut series = String::new();
    for (i, s) in chart.series.iter().enumerate() {
        let col = column(i + 1);
        let end = chart.categories.len() + 1;
        let nums = s
            .values
            .iter()
            .enumerate()
            .map(|(j, v)| format!("<c:pt idx=\"{j}\"><c:v>{v}</c:v></c:pt>"))
            .collect::<String>();
        series.push_str(&format!("<c:ser><c:idx val=\"{i}\"/><c:order val=\"{i}\"/><c:tx><c:strRef><c:f>Sheet1!${col}$1</c:f>{}</c:strRef></c:tx><c:spPr>{}</c:spPr><c:cat><c:strRef><c:f>Sheet1!$A$2:$A${end}</c:f>{}</c:strRef></c:cat><c:val><c:numRef><c:f>Sheet1!${col}$2:${col}${end}</c:f><c:numCache><c:formatCode>General</c:formatCode><c:ptCount val=\"{}\"/>{nums}</c:numCache></c:numRef></c:val></c:ser>",strings(std::slice::from_ref(&s.name)),xml::fill(if i%2==0{&t.accent}else{&t.muted}),strings(&chart.categories),s.values.len()));
    }
    let (tag, config) = match chart.kind {
        ChartKind::Bar => (
            "barChart",
            "<c:barDir val=\"col\"/><c:grouping val=\"clustered\"/>",
        ),
        ChartKind::Line => ("lineChart", "<c:grouping val=\"standard\"/>"),
        ChartKind::Pie => ("pieChart", ""),
    };
    let axes = if chart.kind == ChartKind::Pie {
        String::new()
    } else {
        format!(
            "<c:catAx><c:axId val=\"1\"/><c:scaling><c:orientation val=\"minMax\"/></c:scaling><c:axPos val=\"b\"/><c:txPr><a:bodyPr/><a:lstStyle/>{}</c:txPr><c:crossAx val=\"2\"/><c:crosses val=\"autoZero\"/></c:catAx><c:valAx><c:axId val=\"2\"/><c:scaling><c:orientation val=\"minMax\"/></c:scaling><c:axPos val=\"l\"/><c:numFmt formatCode=\"General\" sourceLinked=\"0\"/><c:txPr><a:bodyPr/><a:lstStyle/>{}</c:txPr><c:crossAx val=\"1\"/><c:crosses val=\"autoZero\"/><c:crossBetween val=\"between\"/></c:valAx>",
            xml::paragraphs(
                &storyboard_core::Text::plain(""),
                12.0,
                &t.foreground,
                &t.font,
                &[]
            ),
            xml::paragraphs(
                &storyboard_core::Text::plain(""),
                12.0,
                &t.foreground,
                &t.font,
                &[]
            )
        )
    };
    let ax_ids = if chart.kind == ChartKind::Pie {
        ""
    } else {
        "<c:axId val=\"1\"/><c:axId val=\"2\"/>"
    };
    format!(
        "{}<c:chartSpace xmlns:c=\"http://schemas.openxmlformats.org/drawingml/2006/chart\" xmlns:a=\"http://schemas.openxmlformats.org/drawingml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\"><c:lang val=\"en-US\"/><c:chart><c:title><c:tx><c:rich><a:bodyPr/><a:lstStyle/>{}</c:rich></c:tx></c:title><c:plotArea><c:layout/><c:{tag}>{config}<c:varyColors val=\"{}\"/>{series}{ax_ids}</c:{tag}>{axes}</c:plotArea><c:legend><c:legendPos val=\"b\"/></c:legend><c:plotVisOnly val=\"1\"/></c:chart><c:spPr>{}</c:spPr><c:externalData r:id=\"rId1\"><c:autoUpdate val=\"0\"/></c:externalData></c:chartSpace>",
        xml::HEADER,
        xml::paragraphs(
            &storyboard_core::Text::plain(&chart.title),
            18.0,
            &t.foreground,
            &t.font,
            &[]
        ),
        u8::from(chart.kind == ChartKind::Pie),
        xml::fill(&t.background)
    )
}
pub fn workbook(chart: &Chart) -> Result<Vec<u8>> {
    let mut parts = BTreeMap::new();
    let mut cells = String::new();
    let headers = std::iter::once("Category").chain(chart.series.iter().map(|s| s.name.as_str()));
    cells.push_str("<row r=\"1\">");
    for (i, h) in headers.enumerate() {
        cells.push_str(&format!(
            "<c r=\"{}1\" t=\"inlineStr\"><is><t>{}</t></is></c>",
            column(i),
            escape(h)
        ));
    }
    cells.push_str("</row>");
    for (i, c) in chart.categories.iter().enumerate() {
        let row = i + 2;
        cells.push_str(&format!(
            "<row r=\"{row}\"><c r=\"A{row}\" t=\"inlineStr\"><is><t>{}</t></is></c>",
            escape(c)
        ));
        for (j, s) in chart.series.iter().enumerate() {
            cells.push_str(&format!(
                "<c r=\"{}{row}\"><v>{}</v></c>",
                column(j + 1),
                s.values[i]
            ));
        }
        cells.push_str("</row>");
    }
    parts.insert("[Content_Types].xml".into(),format!("{}<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\"><Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/><Default Extension=\"xml\" ContentType=\"application/xml\"/><Override PartName=\"/xl/workbook.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml\"/><Override PartName=\"/xl/worksheets/sheet1.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml\"/></Types>",xml::HEADER).into_bytes());
    parts.insert(
        "_rels/.rels".into(),
        package::rels(&[relationship("rId1", "officeDocument", "xl/workbook.xml")]).into_bytes(),
    );
    parts.insert("xl/workbook.xml".into(),format!("{}<workbook xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\" xmlns:r=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships\"><sheets><sheet name=\"Sheet1\" sheetId=\"1\" r:id=\"rId1\"/></sheets></workbook>",xml::HEADER).into_bytes());
    parts.insert(
        "xl/_rels/workbook.xml.rels".into(),
        package::rels(&[relationship("rId1", "worksheet", "worksheets/sheet1.xml")]).into_bytes(),
    );
    parts.insert("xl/worksheets/sheet1.xml".into(),format!("{}<worksheet xmlns=\"http://schemas.openxmlformats.org/spreadsheetml/2006/main\"><sheetData>{cells}</sheetData></worksheet>",xml::HEADER).into_bytes());
    package::zip(&parts)
}
