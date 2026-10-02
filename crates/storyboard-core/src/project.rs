//! Inspectable project envelope. Image paths remain relative to the project directory.
use crate::{Error, MAX_INPUT_BYTES, Result, Story, Theme};
use serde::{Deserialize, Serialize};

pub const MAX_PROJECT_BYTES: usize = 16 * 1024 * 1024;
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Project {
    pub project_version: u32,
    pub id: String,
    pub brief: String,
    pub story: Story,
    pub theme: Theme,
    pub updated_ms: u64,
}
impl Project {
    pub fn validate(&self) -> Result<()> {
        if self.project_version != 1 {
            return Err(Error::Invalid(
                "Unsupported project version; expected 1".into(),
            ));
        }
        if self.id.is_empty()
            || self.id.len() > 80
            || !self
                .id
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || b == b'-')
        {
            return Err(Error::Invalid("Invalid project identifier".into()));
        }
        if self.brief.len() > MAX_INPUT_BYTES {
            return Err(Error::Invalid("Project brief exceeds 8 MiB".into()));
        }
        self.story.validate()?;
        self.theme.validate()?;
        if self.story.presentation.theme != self.theme.name {
            return Err(Error::Invalid(
                "Project story and theme names differ".into(),
            ));
        }
        Ok(())
    }
    pub fn parse(input: &str) -> Result<Self> {
        if input.len() > MAX_PROJECT_BYTES {
            return Err(Error::Invalid("Project exceeds 16 MiB".into()));
        }
        let project: Self = serde_json::from_str(input)?;
        project.validate()?;
        Ok(project)
    }
}
