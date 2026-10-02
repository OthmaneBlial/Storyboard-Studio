use crate::model::*;
use serde::{Deserialize, Serialize};
use std::collections::BTreeSet;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Severity {
    Error,
    Warning,
    Info,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Diagnostic {
    pub code: String,
    pub severity: Severity,
    pub slide: Option<String>,
    pub message: String,
    pub action: String,
}
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Report {
    pub diagnostics_version: String,
    pub findings: Vec<Diagnostic>,
    pub claims: usize,
    pub linked_claims: usize,
    pub author_confirmed_claims: usize,
    pub disclaimer: String,
}
impl Report {
    pub fn markdown(&self) -> String {
        let mut output = format!(
            "# Narrative Doctor\n\n{} findings · {}/{} claims linked · {} author-confirmed\n\n",
            self.findings.len(),
            self.linked_claims,
            self.claims,
            self.author_confirmed_claims
        );
        for f in &self.findings {
            output.push_str(&format!(
                "- **{}** ({:?}, {}): {} {}\n",
                f.code,
                f.severity,
                f.slide.as_deref().unwrap_or("story"),
                f.message,
                f.action
            ));
        }
        output.push_str(&format!("\n{}\n", self.disclaimer));
        output
    }
}
fn words(s: &str) -> BTreeSet<String> {
    s.split(|c: char| !c.is_alphanumeric())
        .filter(|w| w.chars().count() > 2)
        .map(str::to_lowercase)
        .collect()
}
pub fn diagnose(story: &Story) -> Report {
    let mut report = Report { diagnostics_version:"rust-1".into(), findings:Vec::new(), claims:0, linked_claims:0, author_confirmed_claims:0, disclaimer:"Evidence presence and author confirmation do not establish factual truth. No network link checks were performed.".into() };
    let mut add = |code: &str, severity, slide: Option<&Slide>, message: &str, action: &str| {
        report.findings.push(Diagnostic {
            code: code.into(),
            severity,
            slide: slide.map(|s| s.id.clone()),
            message: message.into(),
            action: action.into(),
        })
    };
    if story.audience.trim().is_empty() {
        add(
            "audience.missing",
            Severity::Warning,
            None,
            "Audience is unspecified.",
            "Name who will read or decide.",
        );
    }
    if story.objective.trim().is_empty() {
        add(
            "objective.missing",
            Severity::Warning,
            None,
            "The intended outcome is unspecified.",
            "State what the audience should do or understand.",
        );
    }
    if story.owner.trim().is_empty() {
        add(
            "owner.missing",
            Severity::Error,
            None,
            "No accountable owner.",
            "Assign one owner for the next step.",
        );
    }
    if story.next_action.trim().is_empty() {
        add(
            "action.missing",
            Severity::Error,
            None,
            "No next action is recorded.",
            "Add a concrete action and review point.",
        );
    }
    if !story
        .presentation
        .slides
        .iter()
        .any(|s| s.role == Role::Recommendation)
    {
        add(
            "recommendation.missing",
            Severity::Warning,
            None,
            "No explicit recommendation slide.",
            "State the recommendation and its trade-off.",
        );
    }
    if let Some(first) = story.presentation.slides.first()
        && !matches!(first.role, Role::Context | Role::Problem)
    {
        add(
            "opening.weak",
            Severity::Warning,
            Some(first),
            "The opening jumps into a later story role.",
            "Establish context or tension before the proposed answer.",
        );
    }
    let mut seen = BTreeSet::new();
    for (i, s) in story.presentation.slides.iter().enumerate() {
        let content = s
            .blocks
            .iter()
            .map(Block::text)
            .collect::<Vec<_>>()
            .join(" ");
        if !seen.insert(format!("{} {content}", s.title).to_lowercase()) {
            add(
                "slide.duplicate",
                Severity::Warning,
                Some(s),
                "This slide repeats an earlier slide.",
                "Merge duplicates or give each a distinct purpose.",
            );
        }
        if s.purpose.trim().is_empty() {
            add(
                "purpose.missing",
                Severity::Warning,
                Some(s),
                "The slide has no stated purpose.",
                "Explain how this slide advances the argument.",
            );
        }
        if [
            "overview",
            "introduction",
            "summary",
            "conclusion",
            "untitled",
        ]
        .contains(&s.title.to_lowercase().as_str())
        {
            add(
                "title.vague",
                Severity::Warning,
                Some(s),
                "The title names a topic without a point.",
                "Make the title state the slide's conclusion.",
            );
        }
        if content.split_whitespace().count() > 100 {
            add(
                "copy.dense",
                Severity::Warning,
                Some(s),
                "More than 100 words on this slide.",
                "Move detail into notes or split the argument.",
            );
        }
        if s.blocks.is_empty() {
            add(
                "slide.empty",
                Severity::Warning,
                Some(s),
                "The slide contains no supporting content.",
                "Add author-owned content or remove the slide.",
            );
        }
        let lc = content.to_lowercase();
        if [
            "leverage synergies",
            "in today's rapidly",
            "game-changing",
            "unlock the potential",
            "revolutionize",
            "seamlessly",
        ]
        .iter()
        .any(|p| lc.contains(p))
        {
            add(
                "copy.generic",
                Severity::Info,
                Some(s),
                "Generic promotional language weakens precision.",
                "Replace it with a concrete mechanism or outcome.",
            );
        }
        if i > 0 && i + 1 < story.presentation.slides.len() && s.transition.trim().is_empty() {
            add(
                "transition.missing",
                Severity::Info,
                Some(s),
                "No explicit link to the preceding point.",
                "Record the transition in the story or speaker notes.",
            );
        }
        if s.role == Role::Options
            && s.blocks.len() >= 2
            && words(&s.blocks[0].text()) == words(&s.blocks[1].text())
        {
            add(
                "options.indistinct",
                Severity::Warning,
                Some(s),
                "The options use identical language.",
                "Show a meaningful difference in cost, outcome or risk.",
            );
        }
        for previous in story.presentation.slides.iter().take(i) {
            let a = words(&content);
            let b = words(
                &previous
                    .blocks
                    .iter()
                    .map(Block::text)
                    .collect::<Vec<_>>()
                    .join(" "),
            );
            let union = a.union(&b).count();
            if union >= 8 && a.intersection(&b).count() as f64 / union as f64 > 0.85 {
                add(
                    "slide.similar",
                    Severity::Warning,
                    Some(s),
                    "Content substantially overlaps an earlier slide.",
                    "Give each slide a separate contribution.",
                );
                break;
            }
        }
        if s.claims.is_empty()
            && content.chars().any(|c| c.is_ascii_digit())
            && s.evidence.is_empty()
        {
            add(
                "evidence.numeric-claim",
                Severity::Warning,
                Some(s),
                "Numbers appear without an explicit claim/evidence record.",
                "Record the source or label the number as a synthetic assumption.",
            );
        }
        for claim in &s.claims {
            report.claims += 1;
            let linked: Vec<_> = s
                .evidence
                .iter()
                .filter(|e| e.claim_ids.contains(&claim.id))
                .collect();
            if !linked.is_empty() {
                report.linked_claims += 1;
            }
            if linked.iter().any(|e| e.author_confirmed) {
                report.author_confirmed_claims += 1;
            }
            if linked.is_empty() && !claim.assumption {
                add(
                    "claim.unsupported",
                    Severity::Warning,
                    Some(s),
                    &format!("Claim {} has no linked evidence.", claim.id),
                    "Link an author-owned source or explicitly mark an assumption.",
                );
            }
        }
        for e in &s.evidence {
            if !e.author_confirmed {
                add(
                    "evidence.unreviewed",
                    Severity::Info,
                    Some(s),
                    &format!("{} is present but not author-confirmed.", e.citation.label),
                    "Review the excerpt and record an owner and checked date.",
                );
            }
        }
        if i > 0 && s.role == Role::Context && story.presentation.slides[i - 1].role == Role::Action
        {
            add(
                "progression.backtrack",
                Severity::Warning,
                Some(s),
                "The story returns to context after its action.",
                "Move setup earlier or label this as an appendix.",
            );
        }
        if lc.contains("customer") && lc.contains("client") {
            add(
                "terminology.inconsistent",
                Severity::Info,
                Some(s),
                "Both customer and client appear on the slide.",
                "Confirm whether they mean different groups; otherwise use one term.",
            );
        }
    }
    report
}
