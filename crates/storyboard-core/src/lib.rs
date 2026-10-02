//! Offline presentation compilation. No network, processes or filesystem side effects.
pub mod compiler;
pub mod doctor;
pub mod layout;
pub mod model;
pub mod project;
pub mod theme;

pub use compiler::{compile, compile_markdown, story_markdown};
pub use doctor::{Diagnostic, Report, Severity, diagnose};
pub use layout::{Element, LayoutDeck, LayoutSlide, Rect, resolve};
pub use model::*;
pub use project::Project;
pub use theme::{Theme, themes};

#[derive(Debug, thiserror::Error)]
pub enum Error {
    #[error("Invalid presentation: {0}")]
    Invalid(String),
    #[error("Cannot parse input: {0}")]
    Json(#[from] serde_json::Error),
    #[error("Slide {slide}: {message}")]
    Layout { slide: usize, message: String },
}
pub type Result<T> = std::result::Result<T, Error>;
pub const VERSION: &str = env!("CARGO_PKG_VERSION");
pub const FORMAT_VERSION: &str = "3";
pub const MAX_INPUT_BYTES: usize = 8 * 1024 * 1024;
pub fn schema() -> serde_json::Value {
    schemars::schema_for!(Story).to_value()
}
