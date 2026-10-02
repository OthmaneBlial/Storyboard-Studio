use crate::{Error, FORMAT_VERSION, MAX_INPUT_BYTES, Result, model::*};
use serde::Deserialize;

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Brief {
    #[serde(default)]
    schema_version: Option<String>,
    #[serde(default)]
    template: Option<String>,
    #[serde(default)]
    title: String,
    #[serde(default)]
    decision: String,
    audience: String,
    #[serde(alias = "desired_outcome")]
    objective: String,
    #[serde(alias = "current_context")]
    context: String,
    #[serde(default)]
    problem: String,
    #[serde(default)]
    constraints: Vec<String>,
    #[serde(default)]
    options: Vec<OptionBrief>,
    #[serde(default)]
    trade_offs: Vec<String>,
    #[serde(default)]
    recommendation: String,
    #[serde(default)]
    risks: Vec<String>,
    #[serde(default)]
    evidence: Vec<Source>,
    owner: String,
    #[serde(alias = "next_step")]
    next_action: String,
    #[serde(default)]
    review_date: String,
}
#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct OptionBrief {
    title: String,
    description: String,
}
#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
struct Source {
    label: String,
    #[serde(alias = "excerpt")]
    evidence: String,
    #[serde(default)]
    owner: String,
    #[serde(default)]
    url: String,
    #[serde(default)]
    local_reference: String,
    #[serde(default)]
    checked_date: Option<String>,
    #[serde(default)]
    license: String,
    #[serde(default)]
    review_status: String,
    #[serde(default)]
    claim_ids: Vec<String>,
}
fn slide(index: usize, title: String, role: Role, blocks: Vec<Block>) -> Slide {
    Slide {
        id: format!("slide-{index:03}"),
        purpose: title.clone(),
        title,
        role,
        layout: Layout::Stack,
        blocks,
        claims: Vec::new(),
        evidence: Vec::new(),
        notes: String::new(),
        transition: String::new(),
    }
}
fn text(value: impl Into<String>) -> Block {
    Block::Text {
        text: Text::plain(value),
    }
}
fn story(title: String, slides: Vec<Slide>) -> Story {
    Story {
        schema_version: FORMAT_VERSION.into(),
        presentation: Presentation {
            title,
            subtitle: String::new(),
            theme: "midnight".into(),
            slides,
        },
        audience: String::new(),
        objective: String::new(),
        owner: String::new(),
        next_action: String::new(),
        metadata: Metadata::default(),
    }
}
pub fn compile(input: &str, markdown: bool) -> Result<Story> {
    if input.len() > MAX_INPUT_BYTES {
        return Err(Error::Invalid("Input exceeds 8 MiB".into()));
    }
    if markdown {
        return compile_markdown(input);
    }
    let envelope: serde_json::Value = serde_json::from_str(input)?;
    if envelope.get("presentation").is_some() {
        let story: Story = serde_json::from_value(envelope)?;
        story.validate()?;
        return Ok(story);
    }
    let brief: Brief = serde_json::from_value(envelope)?;
    if brief
        .schema_version
        .as_ref()
        .is_some_and(|v| v != "2" && v != "3")
        || brief
            .template
            .as_ref()
            .is_some_and(|v| v != "decision-brief")
    {
        return Err(Error::Invalid(
            "Unsupported brief version or template".into(),
        ));
    }
    let title = if brief.title.trim().is_empty() {
        brief.decision.clone()
    } else {
        brief.title.clone()
    };
    let mut slides = vec![slide(
        1,
        title.clone(),
        Role::Context,
        vec![
            text(brief.context),
            Block::Callout {
                title: "Objective".into(),
                body: brief.objective.clone(),
            },
        ],
    )];
    if !brief.problem.is_empty() {
        slides.push(slide(
            slides.len() + 1,
            brief.problem.clone(),
            Role::Problem,
            vec![text(brief.problem)],
        ));
    }
    if !brief.constraints.is_empty() {
        slides.push(slide(
            slides.len() + 1,
            "Work within the constraints".into(),
            Role::Implications,
            brief
                .constraints
                .iter()
                .map(|v| Block::Card {
                    title: v.clone(),
                    body: String::new(),
                })
                .collect(),
        ));
    }
    if !brief.evidence.is_empty() {
        let mut s = slide(
            slides.len() + 1,
            "What the evidence supports".into(),
            Role::Evidence,
            brief
                .evidence
                .iter()
                .map(|e| Block::Card {
                    title: e.label.clone(),
                    body: e.evidence.clone(),
                })
                .collect(),
        );
        for (i, source) in brief.evidence.into_iter().enumerate() {
            let id = format!("evidence-{}", i + 1);
            let claim_id = format!("claim-{}", i + 1);
            s.claims.push(Claim {
                id: claim_id.clone(),
                text: source.evidence.clone(),
                assumption: false,
            });
            // Legacy links refer to old slide claims, so relink the authored excerpt explicitly.
            let notes = format!(
                "Legacy claim links: {}. License: {}",
                source.claim_ids.join(", "),
                source.license
            );
            s.notes.push_str(&notes);
            let (kind, reference) = if !source.url.is_empty() {
                (EvidenceKind::Url, source.url)
            } else if !source.local_reference.is_empty() {
                (EvidenceKind::LocalFile, source.local_reference)
            } else {
                (EvidenceKind::Note, source.label.clone())
            };
            s.evidence.push(Evidence {
                id,
                citation: Citation {
                    label: source.label,
                    locator: String::new(),
                    author: String::new(),
                },
                kind,
                reference,
                excerpt: source.evidence,
                owner: source.owner,
                claim_ids: vec![claim_id],
                author_confirmed: source.review_status == "author-checked",
                checked_date: source.checked_date,
            });
        }
        slides.push(s);
    }
    if !brief.options.is_empty() {
        let mut s = slide(
            slides.len() + 1,
            "Compare the possible paths".into(),
            Role::Options,
            brief
                .options
                .into_iter()
                .map(|o| Block::Card {
                    title: o.title,
                    body: o.description,
                })
                .collect(),
        );
        s.layout = Layout::Columns;
        slides.push(s);
    }
    if !brief.trade_offs.is_empty() {
        slides.push(slide(
            slides.len() + 1,
            "The trade-offs to accept".into(),
            Role::Implications,
            brief
                .trade_offs
                .iter()
                .map(|v| Block::Card {
                    title: v.clone(),
                    body: String::new(),
                })
                .collect(),
        ));
    }
    let recommendation = if brief.recommendation.is_empty() {
        brief.decision
    } else {
        brief.recommendation
    };
    if !recommendation.is_empty() {
        slides.push(slide(
            slides.len() + 1,
            recommendation.clone(),
            Role::Recommendation,
            vec![Block::Callout {
                title: "Recommendation".into(),
                body: recommendation,
            }],
        ));
    }
    if !brief.risks.is_empty() {
        slides.push(slide(
            slides.len() + 1,
            "Risks to manage".into(),
            Role::Implications,
            brief
                .risks
                .iter()
                .map(|v| Block::Card {
                    title: v.clone(),
                    body: String::new(),
                })
                .collect(),
        ));
    }
    slides.push(slide(
        slides.len() + 1,
        brief.next_action.clone(),
        Role::Action,
        vec![
            Block::Card {
                title: "Owner".into(),
                body: brief.owner.clone(),
            },
            Block::Card {
                title: "Review".into(),
                body: brief.review_date,
            },
        ],
    ));
    let mut result = story(title, slides);
    result.audience = brief.audience;
    result.objective = brief.objective;
    result.owner = brief.owner;
    result.next_action = brief.next_action;
    result.presentation.subtitle = format!("{} · {}", result.audience, result.objective);
    result.validate()?;
    Ok(result)
}
fn infer_role(title: &str) -> Role {
    let t = title.to_lowercase();
    if ["action", "next", "timeline", "kickoff"]
        .iter()
        .any(|v| t.contains(v))
    {
        Role::Action
    } else if ["recommend", "decision", "proposal"]
        .iter()
        .any(|v| t.contains(v))
    {
        Role::Recommendation
    } else if ["option", "path", "alternative"]
        .iter()
        .any(|v| t.contains(v))
    {
        Role::Options
    } else if ["evidence", "metric", "result"]
        .iter()
        .any(|v| t.contains(v))
    {
        Role::Evidence
    } else if ["problem", "tension", "challenge", "incident"]
        .iter()
        .any(|v| t.contains(v))
    {
        Role::Problem
    } else if ["risk", "trade", "implication", "cost"]
        .iter()
        .any(|v| t.contains(v))
    {
        Role::Implications
    } else {
        Role::Context
    }
}
/// Heading-based Markdown: H1 is the deck title, H2 creates a slide, H3 creates a card.
/// Metadata before the first H2 is authored, never inferred from external data.
pub fn compile_markdown(input: &str) -> Result<Story> {
    if input.len() > MAX_INPUT_BYTES {
        return Err(Error::Invalid("Input exceeds 8 MiB".into()));
    }
    let mut result = story(String::new(), Vec::new());
    let mut body = String::new();
    let mut card_title = None;
    let flush = |slides: &mut Vec<Slide>, body: &mut String, card: &mut Option<String>| {
        if let Some(s) = slides.last_mut() {
            if let Some(title) = card.take() {
                s.blocks.push(Block::Card {
                    title,
                    body: body.trim().into(),
                });
            } else if !body.trim().is_empty() {
                s.blocks.push(text(body.trim()));
            }
        }
        body.clear();
    };
    for line in input.lines() {
        if let Some(title) = line.strip_prefix("# ") {
            if !result.presentation.title.is_empty() || !result.presentation.slides.is_empty() {
                return Err(Error::Invalid(
                    "Use one H1 title before slide headings".into(),
                ));
            }
            result.presentation.title = title.trim().into();
        } else if let Some(title) = line.strip_prefix("## ") {
            flush(&mut result.presentation.slides, &mut body, &mut card_title);
            result.presentation.slides.push(slide(
                result.presentation.slides.len() + 1,
                title.trim().into(),
                infer_role(title),
                Vec::new(),
            ));
        } else if let Some(title) = line.strip_prefix("### ") {
            if result.presentation.slides.is_empty() {
                return Err(Error::Invalid(
                    "Card headings require a preceding H2 slide".into(),
                ));
            }
            flush(&mut result.presentation.slides, &mut body, &mut card_title);
            card_title = Some(title.trim().into());
        } else if result.presentation.slides.is_empty() {
            if let Some((key, value)) = line.split_once(':') {
                let value = value.trim().to_string();
                match key.trim().to_lowercase().as_str() {
                    "audience" => result.audience = value,
                    "objective" => result.objective = value,
                    "owner" => result.owner = value,
                    "next action" | "next_action" => result.next_action = value,
                    "theme" => result.presentation.theme = value,
                    "author" => result.metadata.author = value,
                    "synthetic" => result.metadata.synthetic = value == "true",
                    _ => {
                        result.presentation.subtitle.push_str(line);
                        result.presentation.subtitle.push('\n');
                    }
                }
            } else if !line.trim().is_empty() {
                result.presentation.subtitle.push_str(line);
                result.presentation.subtitle.push('\n');
            }
        } else if let Some(note) = line.strip_prefix("Notes: ") {
            if let Some(s) = result.presentation.slides.last_mut() {
                s.notes.push_str(note);
                s.notes.push('\n');
            }
        } else {
            body.push_str(line);
            body.push('\n');
        }
    }
    flush(&mut result.presentation.slides, &mut body, &mut card_title);
    if result.presentation.slides.is_empty() && !result.presentation.subtitle.trim().is_empty() {
        result.presentation.slides.push(slide(
            1,
            result.presentation.title.clone(),
            Role::Context,
            vec![text(result.presentation.subtitle.trim())],
        ));
    }
    result.validate()?;
    Ok(result)
}
