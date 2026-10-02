use crate::{Error, Result, model::valid_color};
use schemars::JsonSchema;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct Theme {
    pub name: String,
    pub background: String,
    pub foreground: String,
    pub muted: String,
    pub accent: String,
    pub surface: String,
    pub font: String,
    pub title_size: f64,
    pub body_size: f64,
    pub margin: f64,
    pub gap: f64,
}
impl Theme {
    pub fn named(name: &str) -> Result<Self> {
        themes()
            .into_iter()
            .find(|t| t.name == name.to_lowercase())
            .ok_or_else(|| Error::Invalid(format!("Unknown theme {name:?}; run storyboard themes")))
    }
    pub fn validate(&self) -> Result<()> {
        if [
            &self.background,
            &self.foreground,
            &self.muted,
            &self.accent,
            &self.surface,
        ]
        .iter()
        .any(|v| !valid_color(v))
            || self.name.is_empty()
            || self.font.is_empty()
            || self.font.chars().any(char::is_control)
            || !(24.0..=64.0).contains(&self.title_size)
            || !(12.0..=32.0).contains(&self.body_size)
            || !(24.0..=72.0).contains(&self.margin)
            || !(4.0..=40.0).contains(&self.gap)
        {
            return Err(Error::Invalid(
                "Theme colors, font or dimensions are invalid".into(),
            ));
        }
        if contrast(&self.background, &self.foreground) < 4.5
            || contrast(&self.surface, &self.foreground) < 4.5
            || contrast(&self.background, &self.muted) < 4.5
        {
            return Err(Error::Invalid("Theme text requires contrast ≥4.5:1".into()));
        }
        Ok(())
    }
}
pub fn contrast(a: &str, b: &str) -> f64 {
    fn lum(s: &str) -> f64 {
        let mut rgb = [0.0; 3];
        for (i, c) in rgb.iter_mut().enumerate() {
            let x = u8::from_str_radix(&s[i * 2..i * 2 + 2], 16).unwrap_or(0) as f64 / 255.0;
            *c = if x <= 0.04045 {
                x / 12.92
            } else {
                ((x + 0.055) / 1.055).powf(2.4)
            };
        }
        rgb[0] * 0.2126 + rgb[1] * 0.7152 + rgb[2] * 0.0722
    }
    let (x, y) = (lum(a), lum(b));
    (x.max(y) + 0.05) / (x.min(y) + 0.05)
}
pub fn themes() -> Vec<Theme> {
    [
        (
            "minimal", "FAFAF7", "202820", "566052", "336943", "EBEEE7", 36.0, 22.0, 48.0,
        ),
        (
            "editorial",
            "F4EDE0",
            "30251D",
            "68594A",
            "A84729",
            "E9DFCE",
            44.0,
            24.0,
            56.0,
        ),
        (
            "midnight", "141C26", "EFF3F5", "A6B4C2", "9DD8C0", "202D3C", 40.0, 22.0, 48.0,
        ),
        (
            "consulting",
            "FFFFFF",
            "182F48",
            "4F667B",
            "1865A6",
            "EBF1F7",
            34.0,
            20.0,
            44.0,
        ),
        (
            "product", "F6F6FB", "25243A", "636178", "5E4B9E", "E9E7F2", 40.0, 22.0, 48.0,
        ),
        (
            "technical",
            "101C22",
            "E5F0EE",
            "9EB7B6",
            "70DDB6",
            "1A3037",
            32.0,
            20.0,
            40.0,
        ),
        (
            "investor", "0D2425", "F5F2DE", "B6C3AF", "DFCF87", "1A3938", 42.0, 22.0, 52.0,
        ),
        (
            "research", "F8F7F3", "252F3A", "566473", "416A92", "E8ECED", 34.0, 20.0, 52.0,
        ),
        (
            "mono", "F7F7F7", "202020", "595959", "353535", "E8E8E8", 32.0, 20.0, 48.0,
        ),
        (
            "swiss", "FDF9F2", "241F19", "665E53", "B53E25", "ECE5DA", 48.0, 24.0, 56.0,
        ),
        (
            "terminal", "0E1D14", "DEF4DF", "A2C5AA", "7CEC9D", "1A3021", 30.0, 20.0, 40.0,
        ),
        (
            "modern", "F0F4F6", "192C3D", "526778", "226D88", "DFE8ED", 42.0, 22.0, 48.0,
        ),
    ]
    .into_iter()
    .map(
        |(name, bg, fg, muted, accent, surface, title_size, body_size, margin)| Theme {
            name: name.into(),
            background: bg.into(),
            foreground: fg.into(),
            muted: muted.into(),
            accent: accent.into(),
            surface: surface.into(),
            font: "Carlito".into(),
            title_size,
            body_size,
            margin,
            gap: 18.0,
        },
    )
    .collect()
}
#[derive(Debug, Clone, Serialize, Deserialize, JsonSchema)]
#[serde(deny_unknown_fields)]
pub struct BrandKit {
    pub name: String,
    pub theme: Theme,
    #[serde(default)]
    pub logo: Option<crate::model::Image>,
}
