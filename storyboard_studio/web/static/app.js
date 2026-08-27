"use strict";

const state = { presentation: null, story: null, report: null, theme: "midnight", configs: new Map(), history: [], future: [], dirty: false, source: "local", layoutContract: null, layoutReport: null, previewMode: window.innerWidth <= 560 ? "outline" : "canvas", previewModeExplicit: false, zoom: 100, preflightTimer: null, preflightRequest: 0, sourceMaterialName: "pasted-source.txt" };
let themes = {
  midnight: { bg: "#101425", text: "#f7f4ee", muted: "#b8c0d6", accent: "#e5b560", surface: "#1b2136" },
  glacier: { bg: "#f4f8f8", text: "#123544", muted: "#55727a", accent: "#0a7c86", surface: "#e4eff0" },
  ember: { bg: "#25120f", text: "#fff5e7", muted: "#d6b9a8", accent: "#f08a4b", surface: "#38201a" },
  forest: { bg: "#f1f5ee", text: "#1d3829", muted: "#577060", accent: "#438360", surface: "#e0eadd" },
  royal: { bg: "#17151b", text: "#f5ecd8", muted: "#c7b99a", accent: "#c79c54", surface: "#28242d" },
  sakura: { bg: "#fcf4f4", text: "#4d2736", muted: "#846274", accent: "#be526d", surface: "#f7e5e7" },
};
const blockChoices = [
  ["standard", "Standard"],
  ["comparison", "Comparison"],
  ["decision", "Decision"],
  ["timeline", "Timeline"],
  ["metric", "Metric"],
  ["process", "Process"],
  ["quote", "Quote / evidence"],
  ["table", "Table"],
  ["chart", "Local chart"],
  ["image", "Local image"],
];

const byId = (id) => document.getElementById(id);
const topic = byId("topic");
const count = byId("slideCount");
const form = byId("briefForm");
const submit = byId("generateButton");
const progressSection = byId("progressSection");
const previewSection = byId("previewSection");

function text(node, value) {
  node.textContent = value || "";
  return node;
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function stableJson(value) {
  if (Array.isArray(value)) return `[${value.map((item) => stableJson(item === undefined ? null : item)).join(",")}]`;
  if (value && typeof value === "object") {
    return `{${Object.keys(value).filter((key) => value[key] !== undefined).sort().map((key) => `${JSON.stringify(key)}:${stableJson(value[key])}`).join(",")}}`;
  }
  return JSON.stringify(value);
}

function storyToMarkdown(story) {
  const presentation = story.presentation;
  const envelope = Object.fromEntries(Object.entries(story).filter(([key]) => key !== "presentation"));
  const metadata = {
    theme: presentation.theme || "midnight",
    citations_appendix: Boolean(presentation.citations_appendix),
    assets: presentation.assets || [],
    brand_kit: presentation.brand_kit || null,
    story: envelope,
  };
  const lines = [`# ${presentation.title}`, `> ${presentation.subtitle || ""}`, "", `<!-- storyboard:meta ${stableJson(metadata)} -->`, ""];
  presentation.slides.forEach((slide) => {
    lines.push(`## ${String(slide.slide_number).padStart(2, "0")} — ${slide.title} [layout=${slide.layout || "right"}] [block=${slide.block || "standard"}]`, "", slide.content, "");
    if (slide.content_block) lines.push(`<!-- storyboard:content-block ${stableJson(slide.content_block)} -->`);
    lines.push(`<!-- storyboard:sources ${stableJson(slide.sources || [])} -->`);
    lines.push(`<!-- storyboard:notes ${stableJson(slide.speaker_notes || "")} -->`);
    (slide.bullet_points || []).slice(0, 3).forEach((point) => lines.push(`- **${point.title}** — ${point.description}`));
    lines.push("");
  });
  return `${lines.join("\n").trimEnd()}\n`;
}

function markdownToStory(markdown) {
  const lines = markdown.replace(/\r\n?/g, "\n").split("\n");
  const unsupported = (cursor, expectation) => { throw new Error(`Unsupported Markdown construct at line ${cursor + 1}; ${expectation}`); };
  if (!lines.length || !lines[0].startsWith("# ")) unsupported(0, "expected one '# Title' heading");
  const title = lines[0].slice(2).trim();
  let cursor = 1;
  while (cursor < lines.length && !lines[cursor].trim()) cursor += 1;
  let subtitle = "";
  if (cursor < lines.length && lines[cursor].startsWith("> ")) {
    subtitle = lines[cursor].slice(2).trim();
    cursor += 1;
  }
  while (cursor < lines.length && !lines[cursor].trim()) cursor += 1;
  let metadata = {};
  const metaMatch = cursor < lines.length && lines[cursor].match(/^<!-- storyboard:meta (.+) -->$/);
  if (metaMatch) {
    try { metadata = JSON.parse(metaMatch[1]); } catch { unsupported(cursor, "invalid storyboard metadata JSON"); }
    cursor += 1;
  }
  const slidePattern = /^##\s+(\d{1,2})\s+—\s+(.+?)(?:\s+\[layout=(left|right|focus)\])?(?:\s+\[block=(standard|comparison|decision|timeline|metric|process|quote|table|chart|image)\])?\s*$/;
  const slides = [];
  while (cursor < lines.length) {
    if (!lines[cursor].trim()) { cursor += 1; continue; }
    const heading = lines[cursor].match(slidePattern);
    if (!heading) unsupported(cursor, "expected '## 01 — Slide title [layout=…] [block=…]'");
    const [, number, slideTitle, layout = "right", block = "standard"] = heading;
    cursor += 1;
    while (cursor < lines.length && !lines[cursor].trim()) cursor += 1;
    const contentLines = [];
    while (cursor < lines.length && lines[cursor].trim() && !lines[cursor].startsWith("- ") && !lines[cursor].startsWith("<!-- storyboard:")) {
      if (lines[cursor].startsWith("#")) unsupported(cursor, "nested headings are not supported inside a slide");
      contentLines.push(lines[cursor].trim());
      cursor += 1;
    }
    while (cursor < lines.length && !lines[cursor].trim()) cursor += 1;
    let contentBlock = null;
    let sources = [];
    let speakerNotes = "";
    while (cursor < lines.length && lines[cursor].startsWith("<!-- storyboard:")) {
      const comment = lines[cursor];
      const supported = comment.match(/^<!-- storyboard:(content-block|sources|notes) (.+) -->$/);
      if (!supported) unsupported(cursor, "unknown storyboard metadata comment");
      let parsed;
      try { parsed = JSON.parse(supported[2]); } catch { unsupported(cursor, "invalid storyboard metadata JSON"); }
      if (supported[1] === "content-block") contentBlock = parsed;
      else if (supported[1] === "sources") sources = parsed;
      else speakerNotes = parsed;
      cursor += 1;
      while (cursor < lines.length && !lines[cursor].trim()) cursor += 1;
    }
    const bulletPoints = [];
    while (cursor < lines.length && lines[cursor].startsWith("- ")) {
      const bullet = lines[cursor].match(/^-\s+\*\*(.+?)\*\*\s+—\s+(.+?)\s*$/);
      if (!bullet) unsupported(cursor, "expected '- **Label** — description' bullet syntax");
      bulletPoints.push({ label: String(bulletPoints.length + 1).padStart(2, "0"), title: bullet[1], description: bullet[2] });
      cursor += 1;
    }
    if (!contentBlock && bulletPoints.length !== 3) throw new Error(`Slide ${number} must contain exactly three bullets or one typed content block.`);
    const slide = { slide_number: Number(number), title: slideTitle, content: contentLines.join(" "), layout, block, bullet_points: bulletPoints, sources, speaker_notes: speakerNotes };
    if (contentBlock) slide.content_block = contentBlock;
    slides.push(slide);
  }
  const presentation = validateOutline({
    title,
    subtitle,
    theme: metadata.theme || "midnight",
    slides,
    assets: metadata.assets || [],
    brand_kit: metadata.brand_kit || undefined,
    citations_appendix: Boolean(metadata.citations_appendix),
  });
  if (metadata.story) return validateStory({ ...metadata.story, presentation });
  return validateStory({
    schema_version: "2",
    kind: "freeform-outline",
    template: "freeform",
    presentation,
    decision_brief: null,
    planner: "imported",
    provider_warning: "Imported explicitly from presentation Markdown; decision fields were not inferred.",
    author_edits: [],
    finding_dispositions: [],
  });
}

function markDirty(description = "") {
  state.dirty = true;
  if (description && state.story) {
    state.story.author_edits = state.story.author_edits || [];
    if (!state.story.author_edits.includes(description)) state.story.author_edits.push(description);
  }
  const status = byId("saveStatus");
  if (status) text(status, "Unsaved storyboard edits");
}

function commitHistory(previous, description = "Edited presentation content") {
  state.history.push(clone(previous));
  if (state.history.length > 50) state.history.shift();
  state.future = [];
  markDirty(description);
  schedulePreflight();
}

function setPath(path, value) {
  const previous = clone(state.presentation);
  let target = state.presentation;
  path.slice(0, -1).forEach((key) => { target = target[key]; });
  target[path[path.length - 1]] = value;
  commitHistory(previous, `Changed ${path.join(".")}`);
}

function renumberSlides() {
  state.presentation.slides.forEach((slide, index) => { slide.slide_number = index + 1; });
}

function undo() {
  if (!state.history.length) return;
  state.future.push(clone(state.presentation));
  state.presentation = state.history.pop();
  markDirty();
  renderPreview({ presentation: state.presentation, source: state.source });
}

function redo() {
  if (!state.future.length) return;
  state.history.push(clone(state.presentation));
  state.presentation = state.future.pop();
  markDirty();
  renderPreview({ presentation: state.presentation, source: state.source });
}

function create(tag, className, value) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (value !== undefined) text(element, value);
  return element;
}

function setFormError(message = "") {
  const error = byId("formError");
  text(error, message);
  error.hidden = !message;
}

function currentWorkflow() {
  return document.querySelector("input[name=workflow]:checked").value;
}

function setWorkflowMode() {
  const guided = currentWorkflow() === "guided";
  byId("guidedFields").hidden = !guided;
  byId("freeformFields").hidden = guided;
  byId("storyControls").hidden = guided;
  text(byId("generateButton").querySelector("span"), guided ? "Build decision story" : "Build my storyboard");
}

function linesFrom(id) {
  return byId(id).value.split("\n").map((value) => value.trim()).filter(Boolean).slice(0, 3);
}

function requireValue(id, message, minimum = 3) {
  const element = byId(id);
  const value = element.value.trim();
  if (value.length < minimum) {
    setFormError(message);
    element.focus();
    throw new Error("invalid-guided-brief");
  }
  return value;
}

function collectDecisionBrief() {
  const decision = requireValue("decision", "State the decision to make.");
  const audience = requireValue("audience", "Name the decision audience.");
  const desiredOutcome = requireValue("desiredOutcome", "Describe the desired outcome.");
  const currentContext = requireValue("currentContext", "Add the current context.");
  const constraints = linesFrom("constraints");
  const tradeOffs = linesFrom("tradeOffs");
  if (!constraints.length) {
    setFormError("Add at least one decision constraint, one per line.");
    byId("constraints").focus();
    throw new Error("invalid-guided-brief");
  }
  if (!tradeOffs.length) {
    setFormError("Add at least one trade-off, one per line.");
    byId("tradeOffs").focus();
    throw new Error("invalid-guided-brief");
  }
  const options = [1, 2, 3].map((index) => ({
    title: byId(`option${index}Title`).value.trim(),
    description: byId(`option${index}Description`).value.trim(),
  })).filter((option) => option.title || option.description);
  if (options.length < 2 || options.some((option) => option.title.length < 1 || option.description.length < 3)) {
    setFormError("Describe at least two complete options.");
    byId("option1Title").focus();
    throw new Error("invalid-guided-brief");
  }
  const reviewDate = requireValue("reviewDate", "Choose an explicit review date.", 10);
  const evidenceLabel = byId("evidenceLabel").value.trim();
  const owner = requireValue("decisionOwner", "Name one accountable owner.", 2);
  const nextStep = requireValue("nextStep", "Name the concrete next step.");
  return {
    schema_version: "2",
    template: "decision-brief",
    decision,
    audience,
    desired_outcome: desiredOutcome,
    current_context: currentContext,
    constraints,
    options,
    trade_offs: tradeOffs,
    evidence: evidenceLabel ? [{ label: evidenceLabel, evidence: byId("evidenceText").value.trim(), owner: byId("evidenceOwner").value.trim() }] : [],
    owner,
    next_step: nextStep,
    review_date: reviewDate,
  };
}

function currentStory() {
  if (!state.presentation) return null;
  if (!state.story) {
    state.story = {
      schema_version: "2",
      kind: "freeform-outline",
      template: "freeform",
      presentation: state.presentation,
      decision_brief: null,
      planner: state.source === "gemini" ? "gemini" : "local",
      provider_warning: "",
      author_edits: [],
      finding_dispositions: [],
    };
  }
  state.story.presentation = state.presentation;
  return state.story;
}

function configFor(index) {
  return state.configs.get(index) || { focus: "", layout: index % 3 === 0 ? "focus" : "right", block: "standard" };
}

function persistConfigInputs() {
  document.querySelectorAll("[data-slide-index]").forEach((input) => {
    const index = Number(input.dataset.slideIndex);
    const current = configFor(index);
    current[input.dataset.configKey] = input.value;
    state.configs.set(index, current);
  });
}

function buildSlideConfigs() {
  persistConfigInputs();
  const container = byId("slideConfigs");
  container.replaceChildren();
  const total = Number(count.value);
  for (let index = 1; index <= total; index += 1) {
    const config = configFor(index);
    const row = create("div", "slide-config");
    row.append(create("span", "slide-number", String(index).padStart(2, "0")));

    const focus = create("input");
    focus.type = "text";
    focus.maxLength = 180;
    focus.placeholder = `Focus for slide ${index} (optional)`;
    focus.value = config.focus;
    focus.dataset.slideIndex = String(index);
    focus.dataset.configKey = "focus";
    focus.setAttribute("aria-label", `Focus for slide ${index}`);

    const layout = create("select");
    layout.dataset.slideIndex = String(index);
    layout.dataset.configKey = "layout";
    layout.setAttribute("aria-label", `Layout for slide ${index}`);
    [["right", "Editorial frame"], ["left", "Frame on left"], ["focus", "Full focus"]].forEach(([value, label]) => {
      const option = create("option", "", label);
      option.value = value;
      option.selected = value === config.layout;
      layout.append(option);
    });
    row.append(focus, layout);
    const block = create("select");
    block.dataset.slideIndex = String(index);
    block.dataset.configKey = "block";
    block.setAttribute("aria-label", `Editorial block for slide ${index}`);
    blockChoices.filter(([value]) => !["chart", "image"].includes(value)).forEach(([value, label]) => {
      const option = create("option", "", label);
      option.value = value;
      option.selected = value === config.block;
      block.append(option);
    });
    row.append(block);
    container.append(row);
  }
}

function currentConfigs() {
  persistConfigInputs();
  return Array.from({ length: Number(count.value) }, (_, index) => configFor(index + 1));
}

function setProgress(percent, title, message) {
  byId("progressBar").style.width = `${percent}%`;
  text(byId("progressTitle"), title);
  text(byId("progressMessage"), message);
}

function setLoading(loading) {
  submit.disabled = loading;
  submit.querySelector("span").textContent = loading ? "Building your story…" : (currentWorkflow() === "guided" ? "Build decision story" : "Build my storyboard");
  form.setAttribute("aria-busy", String(loading));
}

async function readResponse(response) {
  const payload = await response.json().catch(() => ({}));
  if (response.ok) return payload;
  const detail = Array.isArray(payload.detail) ? payload.detail.map((item) => item.msg).join(" ") : payload.detail;
  throw new Error(detail || "The request could not be completed. Please try again.");
}

async function post(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return readResponse(response);
}

function normalizedColor(value) {
  return `#${String(value || "000000").replace("#", "").toLowerCase()}`;
}

function activePreviewTheme() {
  const kit = state.presentation && state.presentation.brand_kit;
  if (kit && kit.colors) {
    return Object.fromEntries(Object.entries(kit.colors).map(([key, value]) => [key, normalizedColor(value)]));
  }
  return themes[state.theme] || themes.midnight;
}

function fontStack(values) {
  return (values || []).map((value) => value.includes(" ") ? `"${value}"` : value).join(", ");
}

function applyLayoutContract(contract) {
  state.layoutContract = contract;
  themes = Object.fromEntries(Object.entries(contract.themes).map(([id, theme]) => [id, {
    bg: normalizedColor(theme.bg),
    text: normalizedColor(theme.text),
    muted: normalizedColor(theme.muted),
    accent: normalizedColor(theme.accent),
    surface: normalizedColor(theme.surface),
    surfaceAlt: normalizedColor(theme.surface_alt),
  }]));
  const root = document.documentElement;
  root.style.setProperty("--deck-display", fontStack(contract.font_fallbacks.display));
  root.style.setProperty("--deck-body", fontStack(contract.font_fallbacks.body));
  root.style.setProperty("--deck-safe-area", `${(contract.safe_area_inches / contract.canvas.width_inches) * 100}%`);
  text(byId("layoutContractStatus"), `Shared layout v${contract.schema_version} · 16:9 · ${contract.safe_area_inches}\" safe area`);
  root.dataset.layoutReady = "true";
  if (state.presentation) renderPreview({ presentation: state.presentation, source: state.source });
}

async function initializeLayoutContract() {
  try {
    const response = await fetch("/api/v1/layout-contract");
    applyLayoutContract(await readResponse(response));
  } catch (error) {
    document.documentElement.dataset.layoutReady = "fallback";
    text(byId("layoutContractStatus"), "Built-in layout fallback · export contract unavailable");
  }
}

function applyPreviewMode(mode = state.previewMode) {
  state.previewMode = mode;
  const deck = byId("deckPreview");
  deck.dataset.view = mode;
  deck.style.setProperty("--deck-width", `${state.zoom}%`);
  byId("canvasViewButton").setAttribute("aria-pressed", String(mode === "canvas"));
  byId("outlineViewButton").setAttribute("aria-pressed", String(mode === "outline"));
  byId("zoomOutButton").disabled = mode !== "canvas" || state.zoom <= 75;
  byId("zoomInButton").disabled = mode !== "canvas" || state.zoom >= 150;
  text(byId("zoomValue"), `${state.zoom}%`);
}

function setPreviewMode(mode) {
  state.previewModeExplicit = true;
  applyPreviewMode(mode);
}

function setZoom(next) {
  state.zoom = Math.max(75, Math.min(150, next));
  applyPreviewMode();
}

function shortenAtWord(value, limit) {
  if (value.length <= limit) return value;
  const candidate = value.slice(0, Math.max(1, limit - 1));
  const boundary = candidate.lastIndexOf(" ");
  return `${candidate.slice(0, boundary > limit * 0.55 ? boundary : candidate.length).trim()}…`;
}

function splitSlideAtSummary(index) {
  if (state.presentation.slides.length >= 10) return;
  const previous = clone(state.presentation);
  const slide = state.presentation.slides[index];
  const words = slide.content.trim().split(/\s+/);
  const midpoint = Math.ceil(words.length / 2);
  const duplicate = clone(slide);
  slide.content = words.slice(0, midpoint).join(" ");
  duplicate.content = words.slice(midpoint).join(" ");
  slide.title = shortenAtWord(`${slide.title} · 1/2`, 68);
  duplicate.title = shortenAtWord(`${duplicate.title.replace(/ · 1\/2$/, "")} · 2/2`, 68);
  if (slide.content_block && slide.content_block.type === "standard" && slide.content_block.points.length > 1) {
    const pointMidpoint = Math.ceil(slide.content_block.points.length / 2);
    duplicate.content_block.points = duplicate.content_block.points.slice(pointMidpoint);
    slide.content_block.points = slide.content_block.points.slice(0, pointMidpoint);
  }
  state.presentation.slides.splice(index + 1, 0, duplicate);
  renumberSlides();
  commitHistory(previous, `Split slide ${index + 1} at the shared layout boundary`);
  renderPreview({ presentation: state.presentation, source: state.source });
}

function applyOverflowAction(finding, action) {
  const previous = clone(state.presentation);
  const slide = state.presentation.slides[finding.slide_index];
  if (action === "shorten" && ["title", "content"].includes(finding.field)) {
    slide[finding.field] = shortenAtWord(slide[finding.field], finding.limit);
    commitHistory(previous, `Shortened slide ${finding.slide_number} ${finding.field} to fit`);
    renderPreview({ presentation: state.presentation, source: state.source });
  } else if (action === "use-focus") {
    slide.layout = "focus";
    commitHistory(previous, `Changed slide ${finding.slide_number} to focus layout`);
    renderPreview({ presentation: state.presentation, source: state.source });
  } else if (action === "split") {
    splitSlideAtSummary(finding.slide_index);
  } else if (action === "review-block") {
    const card = byId("deckPreview").querySelectorAll(".content-preview")[finding.slide_index];
    const target = card && card.querySelector(".semantic-input");
    if (target) target.focus();
  }
}

function renderLayoutPreflight(report) {
  state.layoutReport = report;
  const panel = byId("layoutPreflight");
  panel.dataset.status = report.status;
  const findings = byId("overflowFindings");
  findings.replaceChildren();
  byId("deckPreview").querySelectorAll(".content-preview").forEach((card) => { card.dataset.overflow = "false"; });
  if (!report.findings.length) {
    text(byId("layoutPreflightTitle"), "Layout ready");
    text(byId("layoutPreflightSummary"), "Shared browser and PowerPoint geometry is within budget.");
    return;
  }
  text(byId("layoutPreflightTitle"), `${report.findings.length} layout ${report.findings.length === 1 ? "fix" : "fixes"} before export`);
  text(byId("layoutPreflightSummary"), "Choose a deterministic fix; Storyboard Studio will not silently shrink or clip this copy.");
  report.findings.forEach((finding) => {
    const card = byId("deckPreview").querySelectorAll(".content-preview")[finding.slide_index];
    if (card) card.dataset.overflow = "true";
    const item = create("article", "overflow-finding");
    item.append(create("p", "", finding.message));
    const actions = create("div", "overflow-actions");
    finding.actions.forEach((action) => {
      const button = create("button", "", action.label);
      button.type = "button";
      button.addEventListener("click", () => applyOverflowAction(finding, action.id));
      actions.append(button);
    });
    item.append(actions);
    findings.append(item);
  });
}

async function runLayoutPreflight() {
  if (!state.presentation) return { status: "ready", findings: [] };
  const request = ++state.preflightRequest;
  const report = await post("/api/v1/layout/preflight", state.presentation);
  if (request === state.preflightRequest) renderLayoutPreflight(report);
  return report;
}

function renderEvidenceCoverage(report) {
  const summary = report.summary;
  text(byId("evidenceCoverageTitle"), `${summary.author_checked_claims}/${summary.claims} claims author checked`);
  text(byId("evidenceCoverageSummary"), `${summary.linked_claims} linked · ${summary.unresolved_claims} unresolved · ${summary.source_entries} source entries. A URL alone never marks a claim as checked.`);
  const list = byId("evidenceCoverageSlides");
  list.replaceChildren();
  report.slides.forEach((slide) => {
    const item = create("li");
    item.dataset.status = slide.unresolved_claims ? "unresolved" : "author-checked";
    item.append(
      create("strong", "", `${String(slide.slide_number).padStart(2, "0")} · ${slide.title}`),
      create("span", "", `${slide.author_checked_claims}/${slide.claims} checked · ${slide.source_entries} sources`),
    );
    list.append(item);
  });
}

async function runEvidenceCoverage() {
  if (!state.presentation) return;
  renderEvidenceCoverage(await post("/api/v1/evidence/coverage", state.presentation));
}

function schedulePreflight() {
  if (!state.presentation) return;
  window.clearTimeout(state.preflightTimer);
  state.preflightTimer = window.setTimeout(() => {
    runLayoutPreflight().catch((error) => {
      text(byId("layoutPreflightTitle"), "Preflight unavailable");
      text(byId("layoutPreflightSummary"), error instanceof Error ? error.message : "Layout preflight failed.");
    });
    runEvidenceCoverage().catch((error) => {
      text(byId("evidenceCoverageTitle"), "Evidence coverage unavailable");
      text(byId("evidenceCoverageSummary"), error instanceof Error ? error.message : "Evidence coverage failed.");
    });
  }, 180);
}

function semanticPlainText(block) {
  if (!block || typeof block !== "object") return "";
  const values = [];
  const add = (...items) => items.forEach((item) => {
    if (typeof item === "string" && item.trim()) values.push(item.trim());
  });
  if (block.type === "standard") {
    (block.points || []).forEach((point) => add(point.title, point.description));
  } else if (block.type === "comparison") {
    (block.sides || []).forEach((side) => add(side.title, side.summary));
    (block.criteria || []).forEach((criterion) => add(criterion.label, criterion.left, criterion.right));
  } else if (block.type === "decision") {
    add(block.decision, block.rationale, block.owner);
    (block.options || []).forEach((option) => add(option.title, option.description));
  } else if (block.type === "timeline") {
    (block.steps || []).forEach((step) => add(step.label, step.title, step.owner));
  } else if (block.type === "metric") {
    add(block.value, block.label, block.context, block.source);
  } else if (block.type === "process") {
    (block.steps || []).forEach((step) => add(step.title, step.description));
  } else if (block.type === "quote") {
    add(block.quote, block.attribution, block.evidence);
  } else if (block.type === "table") {
    (block.columns || []).forEach((column) => add(column));
    (block.rows || []).forEach((row) => (row.cells || []).forEach((cell) => add(cell)));
    add(block.accessible_summary);
  } else if (block.type === "chart") {
    add(block.title, block.chart_type, block.category_field, ...(block.value_fields || []), block.source_note);
  } else if (block.type === "image") {
    add(block.alt_text, block.caption, block.asset_id);
  }
  return values.join(" | ");
}

function legacyPoints(slide) {
  const defaults = [
    { label: "01", title: "Context", description: slide.content || "Add the relevant context." },
    { label: "02", title: "Choice", description: "Describe the option or trade-off." },
    { label: "03", title: "Action", description: "Name the owner and next action." },
  ];
  return defaults.map((fallback, index) => {
    const point = Array.isArray(slide.bullet_points) ? slide.bullet_points[index] : null;
    return point && typeof point === "object" ? { ...fallback, ...point } : fallback;
  });
}

function contentBlockFor(slide, requestedType = slide.block || "standard") {
  if (slide.content_block && slide.content_block.type === requestedType) return slide.content_block;
  const points = legacyPoints(slide);
  const source = Array.isArray(slide.sources) && slide.sources[0] ? slide.sources[0] : {};
  const localAssets = state.presentation && Array.isArray(state.presentation.assets) ? state.presentation.assets : [];
  const dataAsset = localAssets.find((asset) => asset.kind === "data");
  const imageAsset = localAssets.find((asset) => asset.kind === "image");
  const summary = slide.content || "Add the author-owned meaning for this block.";
  const blocks = {
    standard: { type: "standard", points },
    comparison: {
      type: "comparison",
      sides: points.slice(0, 2).map((point) => ({ title: point.title, summary: point.description })),
      criteria: [{ label: points[2].title, left: points[0].description, right: points[1].description }],
    },
    decision: {
      type: "decision",
      decision: summary,
      options: points.slice(0, 2).map((point) => ({ title: point.title, description: point.description })),
      rationale: points[2].description,
      owner: source.owner || "",
    },
    timeline: {
      type: "timeline",
      steps: points.map((point) => ({ label: point.label, title: point.title, owner: source.owner || "" })),
    },
    metric: {
      type: "metric",
      value: points[0].label,
      label: points[0].title,
      context: points[0].description,
      source: source.label || "",
    },
    process: {
      type: "process",
      steps: points.map((point) => ({ title: point.title, description: point.description })),
    },
    quote: {
      type: "quote",
      quote: summary,
      attribution: points[0].title,
      evidence: points[0].description,
    },
    table: {
      type: "table",
      columns: ["Point", "Detail"],
      rows: points.map((point) => ({ cells: [point.title, point.description] })),
      accessible_summary: summary,
    },
    chart: {
      type: "chart",
      chart_type: "bar",
      asset_id: dataAsset ? dataAsset.id : "",
      category_field: "category",
      value_fields: ["value"],
      title: slide.title || "Local chart",
      source_note: dataAsset ? dataAsset.source_note : "",
    },
    image: {
      type: "image",
      asset_id: imageAsset ? imageAsset.id : "",
      alt_text: imageAsset ? imageAsset.alt_text : summary,
      caption: "",
      fit: "contain",
    },
  };
  return blocks[requestedType] || blocks.standard;
}

function ensureContentBlock(slide) {
  if (!slide.content_block || !slide.content_block.type) {
    slide.content_block = contentBlockFor(slide);
  }
  return slide.content_block;
}

function availableBlockChoices() {
  const assets = state.presentation && Array.isArray(state.presentation.assets) ? state.presentation.assets : [];
  return blockChoices.filter(([kind]) => {
    if (kind === "chart") return assets.some((asset) => asset.kind === "data");
    if (kind === "image") return assets.some((asset) => asset.kind === "image");
    return true;
  });
}

function setSlideBlock(index, kind) {
  const previous = clone(state.presentation);
  const slide = state.presentation.slides[index];
  slide.block = kind;
  slide.content_block = contentBlockFor({ ...slide, content_block: null }, kind);
  commitHistory(previous, `Changed slide ${index + 1} semantic block to ${kind}`);
  renderPreview({ presentation: state.presentation, source: state.source });
}

function addSemanticField(container, slideIndex, label, value, path, multiline = false) {
  const wrapper = create("label", "semantic-field");
  wrapper.append(create("span", "", label));
  const control = create(multiline ? "textarea" : "input", "preview-editable semantic-input");
  control.value = value || "";
  control.setAttribute("aria-label", `Slide ${slideIndex} ${label}`);
  if (multiline) control.rows = 2;
  control.addEventListener("change", () => {
    setPath(path, control.value);
    const fallback = container.parentElement.querySelector(".semantic-fallback p");
    if (fallback) text(fallback, semanticPlainText(state.presentation.slides[slideIndex - 1].content_block));
  });
  wrapper.append(control);
  container.append(wrapper);
}

function addSemanticSelect(container, slideIndex, label, value, path, options) {
  const wrapper = create("label", "semantic-field");
  wrapper.append(create("span", "", label));
  const control = create("select", "preview-editable semantic-input");
  control.setAttribute("aria-label", `Slide ${slideIndex} ${label}`);
  options.forEach(([optionValue, optionLabel]) => {
    const option = create("option", "", optionLabel);
    option.value = optionValue;
    option.selected = optionValue === value;
    control.append(option);
  });
  control.addEventListener("change", () => {
    setPath(path, control.value);
    const fallback = container.parentElement.querySelector(".semantic-fallback p");
    if (fallback) text(fallback, semanticPlainText(state.presentation.slides[slideIndex - 1].content_block));
  });
  wrapper.append(control);
  container.append(wrapper);
}

function addSemanticBlockEditor(card, slide, index) {
  const block = ensureContentBlock(slide);
  const editor = create("div", `semantic-editor semantic-${block.type}`);
  editor.setAttribute("role", "group");
  editor.setAttribute("aria-label", `${block.type} block fields for slide ${index}`);
  const root = ["slides", index - 1, "content_block"];
  if (block.type === "standard") {
    block.points.forEach((point, pointIndex) => {
      addSemanticField(editor, index, `point ${pointIndex + 1} title`, point.title, [...root, "points", pointIndex, "title"]);
      addSemanticField(editor, index, `point ${pointIndex + 1} detail`, point.description, [...root, "points", pointIndex, "description"]);
    });
  } else if (block.type === "comparison") {
    block.sides.forEach((side, sideIndex) => {
      addSemanticField(editor, index, `side ${sideIndex + 1} title`, side.title, [...root, "sides", sideIndex, "title"]);
      addSemanticField(editor, index, `side ${sideIndex + 1} summary`, side.summary, [...root, "sides", sideIndex, "summary"]);
    });
    block.criteria.forEach((criterion, criterionIndex) => {
      addSemanticField(editor, index, `criterion ${criterionIndex + 1} label`, criterion.label, [...root, "criteria", criterionIndex, "label"]);
      addSemanticField(editor, index, `criterion ${criterionIndex + 1} left`, criterion.left, [...root, "criteria", criterionIndex, "left"]);
      addSemanticField(editor, index, `criterion ${criterionIndex + 1} right`, criterion.right, [...root, "criteria", criterionIndex, "right"]);
    });
  } else if (block.type === "decision") {
    addSemanticField(editor, index, "decision statement", block.decision, [...root, "decision"], true);
    block.options.forEach((option, optionIndex) => {
      addSemanticField(editor, index, `option ${optionIndex + 1} title`, option.title, [...root, "options", optionIndex, "title"]);
      addSemanticField(editor, index, `option ${optionIndex + 1} detail`, option.description, [...root, "options", optionIndex, "description"]);
    });
    addSemanticField(editor, index, "decision rationale", block.rationale, [...root, "rationale"], true);
    addSemanticField(editor, index, "decision owner", block.owner, [...root, "owner"]);
  } else if (block.type === "timeline") {
    block.steps.forEach((step, stepIndex) => {
      addSemanticField(editor, index, `step ${stepIndex + 1} label`, step.label, [...root, "steps", stepIndex, "label"]);
      addSemanticField(editor, index, `step ${stepIndex + 1} title`, step.title, [...root, "steps", stepIndex, "title"]);
      addSemanticField(editor, index, `step ${stepIndex + 1} owner`, step.owner, [...root, "steps", stepIndex, "owner"]);
    });
  } else if (block.type === "metric") {
    addSemanticField(editor, index, "metric value", block.value, [...root, "value"]);
    addSemanticField(editor, index, "metric label", block.label, [...root, "label"]);
    addSemanticField(editor, index, "metric context", block.context, [...root, "context"], true);
    addSemanticField(editor, index, "metric source", block.source, [...root, "source"]);
  } else if (block.type === "process") {
    block.steps.forEach((step, stepIndex) => {
      addSemanticField(editor, index, `process step ${stepIndex + 1} title`, step.title, [...root, "steps", stepIndex, "title"]);
      addSemanticField(editor, index, `process step ${stepIndex + 1} detail`, step.description, [...root, "steps", stepIndex, "description"]);
    });
  } else if (block.type === "quote") {
    addSemanticField(editor, index, "quote", block.quote, [...root, "quote"], true);
    addSemanticField(editor, index, "quote attribution", block.attribution, [...root, "attribution"]);
    addSemanticField(editor, index, "quote evidence", block.evidence, [...root, "evidence"], true);
  } else if (block.type === "table") {
    block.columns.forEach((column, columnIndex) => {
      addSemanticField(editor, index, `column ${columnIndex + 1}`, column, [...root, "columns", columnIndex]);
    });
    block.rows.forEach((row, rowIndex) => row.cells.forEach((cell, columnIndex) => {
      addSemanticField(editor, index, `row ${rowIndex + 1} cell ${columnIndex + 1}`, cell, [...root, "rows", rowIndex, "cells", columnIndex]);
    }));
    addSemanticField(editor, index, "table summary", block.accessible_summary, [...root, "accessible_summary"], true);
  } else if (block.type === "chart") {
    const dataAssets = (state.presentation.assets || []).filter((asset) => asset.kind === "data");
    addSemanticSelect(editor, index, "chart type", block.chart_type, [...root, "chart_type"], [["bar", "Bar"], ["line", "Line"], ["donut", "Donut"]]);
    addSemanticSelect(editor, index, "chart asset", block.asset_id, [...root, "asset_id"], dataAssets.map((asset) => [asset.id, asset.id]));
    addSemanticField(editor, index, "chart title", block.title, [...root, "title"]);
    addSemanticField(editor, index, "category field", block.category_field, [...root, "category_field"]);
    block.value_fields.forEach((field, fieldIndex) => {
      addSemanticField(editor, index, `value field ${fieldIndex + 1}`, field, [...root, "value_fields", fieldIndex]);
    });
    addSemanticField(editor, index, "chart source note", block.source_note, [...root, "source_note"], true);
  } else if (block.type === "image") {
    const imageAssets = (state.presentation.assets || []).filter((asset) => asset.kind === "image");
    addSemanticSelect(editor, index, "image asset", block.asset_id, [...root, "asset_id"], imageAssets.map((asset) => [asset.id, asset.id]));
    addSemanticField(editor, index, "image alt text", block.alt_text, [...root, "alt_text"], true);
    addSemanticField(editor, index, "image caption", block.caption, [...root, "caption"]);
    addSemanticSelect(editor, index, "image fit", block.fit, [...root, "fit"], [["contain", "Contain"], ["cover", "Cover"]]);
  }
  card.append(editor);
  const fallback = create("details", "semantic-fallback");
  fallback.append(create("summary", "", "Plain-text block"), create("p", "", semanticPlainText(block)));
  card.append(fallback);

  const assetId = block.asset_id;
  const asset = assetId && (state.presentation.assets || []).find((item) => item.id === assetId);
  if (asset) {
    const provenance = create("p", "asset-provenance");
    provenance.setAttribute("aria-label", `Asset provenance for slide ${index}`);
    text(provenance, `LOCAL ${asset.kind.toUpperCase()} · ${asset.id} · SHA-256 ${asset.sha256.slice(0, 12)}… · ${asset.license} · ${asset.attribution}`);
    card.append(provenance);
  }
}

function claimChoicesForSlide(slide) {
  const choices = [["summary", "Slide summary"]];
  const block = contentBlockFor(slide);
  let count = 0;
  if (block.type === "standard") count = (block.points || []).length;
  else if (block.type === "comparison") count = (block.sides || []).length + (block.criteria || []).length;
  else if (block.type === "decision") count = 2 + (block.options || []).length;
  else if (["timeline", "process"].includes(block.type)) count = (block.steps || []).length;
  else count = 1;
  for (let index = 1; index <= count; index += 1) choices.push([`block-${index}`, `Block claim ${index}`]);
  return choices;
}

function sourceDefaults() {
  return {
    label: "Author source",
    evidence: "",
    owner: "",
    url: "",
    local_reference: "",
    checked_date: null,
    license: "",
    review_status: "unresolved",
    claim_ids: ["summary"],
  };
}

function renderSourceMaterialTargets() {
  const slideSelect = byId("sourceMaterialSlide");
  const claimSelect = byId("sourceMaterialClaim");
  const previousSlide = slideSelect.value;
  slideSelect.replaceChildren();
  (state.presentation?.slides || []).forEach((slide, index) => {
    const option = create("option", "", `${String(index + 1).padStart(2, "0")} · ${slide.title}`);
    option.value = String(index);
    slideSelect.append(option);
  });
  if ([...slideSelect.options].some((option) => option.value === previousSlide)) slideSelect.value = previousSlide;
  const slide = state.presentation?.slides[Number(slideSelect.value || 0)];
  claimSelect.replaceChildren();
  if (!slide) return;
  claimChoicesForSlide(slide).forEach(([claimId, claimLabel]) => {
    const option = create("option", "", `${claimId} · ${claimLabel}`);
    option.value = claimId;
    claimSelect.append(option);
  });
}

function selectedSourceBoundary() {
  const textarea = byId("sourceMaterialText");
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;
  if (start === end) return null;
  const excerpt = textarea.value.slice(start, end).trim();
  if (!excerpt) return null;
  const startLine = textarea.value.slice(0, start).split("\n").length;
  const endLine = startLine + textarea.value.slice(start, end).split("\n").length - 1;
  return { excerpt, startLine, endLine };
}

function updateSourceBoundaryStatus() {
  const boundary = selectedSourceBoundary();
  text(
    byId("sourceMaterialBoundary"),
    boundary
      ? `${state.sourceMaterialName} · lines ${boundary.startLine}–${boundary.endLine} · ${boundary.excerpt.length} characters`
      : `${state.sourceMaterialName} · no excerpt selected`,
  );
}

function safeSourceMaterialName(name) {
  const basename = name.split(/[\\/]/).pop().normalize("NFKD").replace(/[^a-zA-Z0-9._-]+/g, "-").replace(/^-+|-+$/g, "");
  return (basename || "pasted-source.txt").slice(0, 100);
}

function mapSelectedSourceExcerpt() {
  if (!state.presentation) return;
  const boundary = selectedSourceBoundary();
  if (!boundary) {
    text(byId("sourceMaterialStatus"), "Select an exact excerpt in the source text before mapping it.");
    byId("sourceMaterialText").focus();
    return;
  }
  if (boundary.excerpt.length > 300) {
    text(byId("sourceMaterialStatus"), "The selected excerpt is longer than 300 characters. Select a tighter claim-sized passage.");
    return;
  }
  const slideIndex = Number(byId("sourceMaterialSlide").value);
  const slide = state.presentation.slides[slideIndex];
  if (!slide || (slide.sources || []).length >= 6) {
    text(byId("sourceMaterialStatus"), "That slide already has the maximum six source entries.");
    return;
  }
  const label = byId("sourceMaterialLabel").value.trim() || state.sourceMaterialName;
  const claimId = byId("sourceMaterialClaim").value;
  const previous = clone(state.presentation);
  slide.sources = slide.sources || [];
  slide.sources.push({
    ...sourceDefaults(),
    label,
    evidence: boundary.excerpt,
    local_reference: `source-material/${safeSourceMaterialName(state.sourceMaterialName)}#L${boundary.startLine}-L${boundary.endLine}`,
    claim_ids: [claimId],
  });
  commitHistory(previous, `Mapped local source excerpt to slide ${slideIndex + 1} claim ${claimId}`);
  renderPreview({ presentation: state.presentation, story: state.story, source: state.source });
  text(byId("sourceMaterialStatus"), `Mapped ${state.sourceMaterialName} lines ${boundary.startLine}–${boundary.endLine} to slide ${slideIndex + 1} claim ${claimId}.`);
}

function updateSlideSource(slideIndex, sourceIndex, field, value) {
  const previous = clone(state.presentation);
  const source = state.presentation.slides[slideIndex].sources[sourceIndex];
  source[field] = value;
  commitHistory(previous, `Changed evidence ${field} on slide ${slideIndex + 1}`);
}

function toggleSourceClaim(slideIndex, sourceIndex, claimId, checked) {
  const previous = clone(state.presentation);
  const source = state.presentation.slides[slideIndex].sources[sourceIndex];
  const ids = new Set(source.claim_ids || []);
  if (checked) ids.add(claimId);
  else ids.delete(claimId);
  source.claim_ids = [...ids];
  commitHistory(previous, `Changed claim links on slide ${slideIndex + 1}`);
}

function addSourceField(container, slideIndex, sourceIndex, label, field, value, options = {}) {
  const wrapper = create("label", `source-field${options.wide ? " source-field-wide" : ""}`);
  wrapper.append(create("span", "", label));
  const input = create(options.multiline ? "textarea" : (options.select ? "select" : "input"));
  input.className = "evidence-input";
  if (options.type) input.type = options.type;
  if (options.placeholder) input.placeholder = options.placeholder;
  const firstSourceLabel = sourceIndex === 0 && options.firstAria;
  input.setAttribute("aria-label", firstSourceLabel || `${label} for slide ${slideIndex + 1} source ${sourceIndex + 1}`);
  if (options.select) {
    options.select.forEach(([optionValue, optionLabel]) => {
      const option = create("option", "", optionLabel);
      option.value = optionValue;
      option.selected = optionValue === value;
      input.append(option);
    });
  } else {
    input.value = value || "";
    if (options.maxLength) input.maxLength = options.maxLength;
  }
  input.addEventListener("change", () => updateSlideSource(slideIndex, sourceIndex, field, input.value || (options.type === "date" ? null : "")));
  wrapper.append(input);
  container.append(wrapper);
}

function addEvidenceEditor(card, slide, index) {
  slide.sources = Array.isArray(slide.sources) ? slide.sources : [];
  const editor = create("details", "evidence-editor");
  editor.open = slide.sources.length > 0;
  editor.append(create("summary", "", `Evidence · ${slide.sources.length} source${slide.sources.length === 1 ? "" : "s"}`));
  const intro = create("p", "evidence-disclaimer", "Link sources to claims explicitly. A URL alone never marks a claim as checked.");
  editor.append(intro);
  slide.sources.forEach((source, sourceIndex) => {
    const sourceCard = create("section", "source-card");
    sourceCard.append(create("h4", "", `Source ${sourceIndex + 1}`));
    addSourceField(sourceCard, index - 1, sourceIndex, "Label", "label", source.label, { maxLength: 100, firstAria: `Source or evidence for slide ${index}` });
    addSourceField(sourceCard, index - 1, sourceIndex, "Excerpt / evidence", "evidence", source.evidence, { multiline: true, wide: true, maxLength: 300 });
    addSourceField(sourceCard, index - 1, sourceIndex, "Owner", "owner", source.owner, { maxLength: 80, firstAria: `Evidence owner for slide ${index}` });
    addSourceField(sourceCard, index - 1, sourceIndex, "Public URL", "url", source.url, { type: "url", maxLength: 500, placeholder: "https://example.org/report" });
    addSourceField(sourceCard, index - 1, sourceIndex, "Local reference", "local_reference", source.local_reference, { maxLength: 240, placeholder: "research/interviews.md#finding" });
    addSourceField(sourceCard, index - 1, sourceIndex, "Checked date", "checked_date", source.checked_date, { type: "date" });
    addSourceField(sourceCard, index - 1, sourceIndex, "License", "license", source.license, { maxLength: 100 });
    addSourceField(sourceCard, index - 1, sourceIndex, "Review status", "review_status", source.review_status || "unresolved", { select: [["unresolved", "Unresolved"], ["author-checked", "Author checked"]] });
    const claims = create("fieldset", "source-claims");
    claims.append(create("legend", "", "Claims supported"));
    claimChoicesForSlide(slide).forEach(([claimId, claimLabel]) => {
      const label = create("label");
      const checkbox = create("input");
      checkbox.type = "checkbox";
      checkbox.checked = (source.claim_ids || []).includes(claimId);
      checkbox.setAttribute("aria-label", `${claimLabel} for slide ${index} source ${sourceIndex + 1}`);
      checkbox.addEventListener("change", () => toggleSourceClaim(index - 1, sourceIndex, claimId, checkbox.checked));
      label.append(checkbox, create("span", "", claimLabel));
      claims.append(label);
    });
    sourceCard.append(claims);
    const remove = create("button", "remove-source", "Remove source");
    remove.type = "button";
    remove.addEventListener("click", () => {
      const previous = clone(state.presentation);
      state.presentation.slides[index - 1].sources.splice(sourceIndex, 1);
      commitHistory(previous, `Removed evidence source from slide ${index}`);
      renderPreview({ presentation: state.presentation, source: state.source });
    });
    sourceCard.append(remove);
    editor.append(sourceCard);
  });
  if (slide.sources.length < 6) {
    const add = create("button", "add-source", "Add source");
    add.type = "button";
    add.addEventListener("click", () => {
      const previous = clone(state.presentation);
      state.presentation.slides[index - 1].sources.push(sourceDefaults());
      commitHistory(previous, `Added evidence source to slide ${index}`);
      renderPreview({ presentation: state.presentation, source: state.source });
    });
    editor.append(add);
  }
  card.append(editor);
}

function addCitationsPreview(container) {
  const colors = activePreviewTheme();
  const citations = state.presentation.slides.flatMap((slide) => slide.sources || []).filter((source) => source.review_status === "author-checked");
  const card = create("article", "slide-preview appendix-preview");
  card.dataset.layout = "focus";
  card.style.setProperty("--preview-bg", colors.bg);
  card.style.setProperty("--preview-text", colors.text);
  card.style.setProperty("--preview-muted", colors.muted);
  card.style.setProperty("--preview-accent", colors.accent);
  card.style.setProperty("--preview-surface", colors.surface);
  card.append(create("span", "preview-index", "STORYBOARD / CITATIONS"), create("h3", "appendix-title", "Citations & evidence"));
  const disclaimer = create("p", "appendix-disclaimer", "Only author-checked entries appear here. Presence does not establish factual truth.");
  card.append(disclaimer);
  const list = create("ol", "appendix-citations");
  (citations.length ? citations : [{ label: "No author-approved citations yet", evidence: "Resolve evidence or disable this appendix." }]).slice(0, 5).forEach((source) => {
    const item = create("li");
    item.append(create("strong", "", source.label), create("span", "", [source.evidence, source.url || source.local_reference, source.owner].filter(Boolean).join(" · ")));
    list.append(item);
  });
  card.append(list);
  container.append(card);
}

function addPreviewSlide(container, slide, index, isTitle = false) {
  const colors = activePreviewTheme();
  const card = create("article", `slide-preview${isTitle ? " title-preview" : " content-preview"}`);
  card.dataset.layout = isTitle ? "focus" : (slide.layout || "right");
  card.style.setProperty("--preview-bg", colors.bg);
  card.style.setProperty("--preview-text", colors.text);
  card.style.setProperty("--preview-muted", colors.muted);
  card.style.setProperty("--preview-accent", colors.accent);
  card.style.setProperty("--preview-surface", colors.surface);
  const kit = state.presentation && state.presentation.brand_kit;
  const displayFonts = kit ? kit.display_font_fallbacks : state.layoutContract && state.layoutContract.font_fallbacks.display;
  const bodyFonts = kit ? kit.body_font_fallbacks : state.layoutContract && state.layoutContract.font_fallbacks.body;
  if (displayFonts) card.style.setProperty("--preview-display", fontStack(displayFonts));
  if (bodyFonts) card.style.setProperty("--preview-body", fontStack(bodyFonts));
  card.append(create("span", "preview-index", isTitle ? "STORYBOARD / TITLE" : `STORYBOARD / ${String(index).padStart(2, "0")}`));
  if (!isTitle) {
    const visual = create("div", "preview-visual-label");
    const blockLabel = (blockChoices.find(([value]) => value === (slide.block || "standard")) || ["", "Key frame"])[1];
    visual.append(create("strong", "", String(index).padStart(2, "0")), create("span", "", blockLabel));
    card.append(visual);
  }
  const title = create("textarea", "preview-editable preview-title-edit");
  title.value = slide.title || "";
  title.rows = isTitle ? 3 : 2;
  title.setAttribute("aria-label", isTitle ? "Presentation title" : `Slide ${index} title`);
  title.addEventListener("change", () => setPath(isTitle ? ["title"] : ["slides", index - 1, "title"], title.value));
  card.append(title);
  const body = create("textarea", "preview-editable preview-body-edit");
  body.value = slide.content || slide.subtitle || "";
  body.rows = 2;
  body.setAttribute("aria-label", isTitle ? "Presentation subtitle" : `Slide ${index} summary`);
  body.addEventListener("change", () => setPath(isTitle ? ["subtitle"] : ["slides", index - 1, "content"], body.value));
  card.append(body);
  if (!isTitle) {
    addSemanticBlockEditor(card, slide, index);
    addEvidenceEditor(card, slide, index);
    const controls = create("div", "slide-controls");
    const layout = create("select", "mini-select");
    layout.setAttribute("aria-label", `Layout for slide ${index}`);
    [["right", "Frame right"], ["left", "Frame left"], ["focus", "Focus frame"]].forEach(([value, label]) => {
      const option = create("option", "", label);
      option.value = value;
      option.selected = value === slide.layout;
      layout.append(option);
    });
    layout.addEventListener("change", () => setPath(["slides", index - 1, "layout"], layout.value));
    controls.append(layout);
    const block = create("select", "mini-select");
    block.setAttribute("aria-label", `Editorial block for slide ${index}`);
    availableBlockChoices().forEach(([value, label]) => {
      const option = create("option", "", label);
      option.value = value;
      option.selected = value === (slide.block || "standard");
      block.append(option);
    });
    block.addEventListener("change", () => setSlideBlock(index - 1, block.value));
    controls.append(block);
    [["↑", "Move slide up", () => moveSlide(index - 1, -1)], ["↓", "Move slide down", () => moveSlide(index - 1, 1)], ["Duplicate", "Duplicate slide", () => duplicateSlide(index - 1)], ["Delete", "Delete slide", () => deleteSlide(index - 1)]].forEach(([label, aria, handler]) => {
      const button = create("button", "mini-button", label);
      button.type = "button";
      button.setAttribute("aria-label", aria);
      button.addEventListener("click", handler);
      controls.append(button);
    });
    card.append(controls);
  }
  container.append(card);
}

function moveSlide(index, direction) {
  const target = index + direction;
  if (target < 0 || target >= state.presentation.slides.length) return;
  const previous = clone(state.presentation);
  [state.presentation.slides[index], state.presentation.slides[target]] = [state.presentation.slides[target], state.presentation.slides[index]];
  renumberSlides();
  commitHistory(previous, `Moved slide ${index + 1} to position ${target + 1}`);
  renderPreview({ presentation: state.presentation, source: state.source });
}

function duplicateSlide(index) {
  if (state.presentation.slides.length >= 10) return;
  const previous = clone(state.presentation);
  state.presentation.slides.splice(index + 1, 0, clone(state.presentation.slides[index]));
  renumberSlides();
  commitHistory(previous, `Duplicated slide ${index + 1}`);
  renderPreview({ presentation: state.presentation, source: state.source });
}

function deleteSlide(index) {
  if (state.presentation.slides.length <= 3) return;
  const previous = clone(state.presentation);
  state.presentation.slides.splice(index, 1);
  renumberSlides();
  commitHistory(previous, `Deleted slide ${index + 1}`);
  renderPreview({ presentation: state.presentation, source: state.source });
}

function renderStoryMap() {
  const map = byId("storyMap");
  map.replaceChildren();
  if (!state.presentation) return;
  state.presentation.slides.forEach((slide) => {
    const item = create("li");
    item.append(create("strong", "", slide.title), create("small", "", `${(slide.block || "standard").toUpperCase()} → ${slide.content}`));
    map.append(item);
  });
  if (state.presentation.citations_appendix) {
    const item = create("li");
    item.append(create("strong", "", "Citations & evidence"), create("small", "", "APPENDIX → author-checked entries only"));
    map.append(item);
  }
}

function dispositionFor(finding) {
  const story = currentStory();
  return story.finding_dispositions.find((item) => item.code === finding.code && item.path === finding.path);
}

function setDisposition(finding, status, reason = "") {
  const story = currentStory();
  const existing = dispositionFor(finding);
  const value = { code: finding.code, path: finding.path, status, reason };
  if (existing) Object.assign(existing, value);
  else story.finding_dispositions.push(value);
  markDirty(`${status} Doctor finding ${finding.code} at ${finding.path}`);
}

function focusFinding(finding) {
  if (finding.slide_number) {
    const sourceFinding = finding.path.includes("sources");
    if (sourceFinding && !state.presentation.slides[finding.slide_number - 1].sources.length) {
      const previous = clone(state.presentation);
      state.presentation.slides[finding.slide_number - 1].sources.push(sourceDefaults());
      commitHistory(previous, `Added a source for Doctor finding on slide ${finding.slide_number}`);
      renderPreview({ presentation: state.presentation, source: state.source });
    }
    const label = sourceFinding ? `Evidence owner for slide ${finding.slide_number}` : `Slide ${finding.slide_number} title`;
    const target = byId("deckPreview").querySelector(`[aria-label="${label}"]`);
    if (target) target.focus();
    return;
  }
  const target = finding.path === "subtitle" ? byId("deckPreview").querySelector('[aria-label="Presentation subtitle"]') : byId("deckPreview").querySelector('[aria-label="Presentation title"]');
  if (target) target.focus();
}

function renderDoctor(report) {
  state.report = report;
  const summary = report.summary;
  text(byId("doctorSummary"), `${summary.errors} errors · ${summary.warnings} warnings · ${summary.information} notes · ${summary.open_findings ?? report.findings.length} open · ${summary.author_checked_claims}/${summary.claims} claims author checked. Structural review only; factual truth is not verified.`);
  const container = byId("doctorFindings");
  container.replaceChildren();
  if (!report.findings.length) {
    container.append(create("p", "doctor-clear", "No structural findings in the current story."));
    return;
  }
  report.findings.forEach((finding) => {
    const card = create("article", "doctor-finding");
    card.dataset.severity = finding.severity;
    const disposition = dispositionFor(finding);
    card.append(
      create("h4", "", `${finding.severity} · ${finding.code}`),
      create("p", "", finding.message),
      create("p", "doctor-action", `Author action: ${finding.action}`),
    );
    if (disposition) card.append(create("p", "", `Disposition: ${disposition.status}${disposition.reason ? ` — ${disposition.reason}` : ""}`));
    const controls = create("div", "finding-controls");
    const reason = create("input");
    reason.placeholder = "Reason for ignore / resolution";
    reason.setAttribute("aria-label", `Disposition reason for ${finding.code} at ${finding.path}`);
    const accept = create("button", "", "Accept action");
    accept.type = "button";
    accept.addEventListener("click", () => {
      setDisposition(finding, "accepted", "");
      focusFinding(finding);
      renderDoctor(report);
    });
    const ignore = create("button", "", "Ignore");
    ignore.type = "button";
    ignore.addEventListener("click", () => {
      if (!reason.value.trim()) {
        reason.setCustomValidity("Explain why this finding is ignored.");
        reason.reportValidity();
        return;
      }
      reason.setCustomValidity("");
      setDisposition(finding, "ignored", reason.value.trim());
      renderDoctor(report);
    });
    const resolve = create("button", "", "Mark resolved");
    resolve.type = "button";
    resolve.addEventListener("click", () => {
      setDisposition(finding, "resolved", reason.value.trim());
      renderDoctor(report);
    });
    controls.append(reason, accept, ignore, resolve);
    card.append(controls);
    container.append(card);
  });
}

async function runDoctor() {
  const button = byId("doctorButton");
  if (!currentStory()) return;
  button.disabled = true;
  text(button, "Reviewing locally…");
  try {
    renderDoctor(await post("/api/v1/stories/doctor", currentStory()));
  } catch (error) {
    text(byId("doctorSummary"), error instanceof Error ? error.message : "The Doctor could not review this story.");
  } finally {
    button.disabled = false;
    text(button, "Run Narrative Doctor");
  }
}

function renderPreview(result) {
  const presentation = result.presentation;
  const isNewPresentation = state.presentation !== presentation;
  if (isNewPresentation) {
    state.history = [];
    state.future = [];
    state.dirty = false;
    state.story = result.story || null;
    state.report = null;
  } else if (result.story) {
    state.story = result.story;
  }
  state.source = result.source || state.source;
  state.presentation = presentation;
  if (isNewPresentation && presentation.theme) state.theme = presentation.theme;
  document.querySelectorAll("input[name=theme]").forEach((input) => { input.checked = input.value === state.theme; });
  document.querySelectorAll(".theme-option").forEach((label) => label.classList.toggle("selected", Boolean(label.querySelector("input:checked"))));
  currentStory();
  presentation.theme = state.theme;
  text(byId("previewTitle"), presentation.title);
  text(byId("previewSubtitle"), presentation.subtitle);
  text(byId("previewSource"), result.source === "gemini" ? "GEMINI-ASSISTED OUTLINE" : (state.story && state.story.kind === "decision-brief" ? "LOCAL DECISION STORY" : "LOCAL EDITABLE OUTLINE"));
  const notice = byId("generationNotice");
  const provider = result.source === "gemini" ? "Gemini-assisted draft" : "Deterministic local draft";
  text(notice, result.warning || `${provider}. Verify unsourced claims and add evidence before sharing. Your export expires from this computer after 24 hours.`);
  notice.hidden = false;
  const deck = byId("deckPreview");
  deck.replaceChildren();
  applyPreviewMode();
  addPreviewSlide(deck, { title: presentation.title, subtitle: presentation.subtitle }, 0, true);
  presentation.slides.forEach((slide, index) => addPreviewSlide(deck, slide, index + 1));
  if (presentation.citations_appendix) addCitationsPreview(deck);
  renderStoryMap();
  renderSourceMaterialTargets();
  const saveStatus = byId("saveStatus");
  if (saveStatus && !state.dirty) text(saveStatus, "No edits yet");
  previewSection.hidden = false;
  byId("clearBrandKitButton").hidden = !presentation.brand_kit;
  byId("citationsButton").setAttribute("aria-pressed", String(Boolean(presentation.citations_appendix)));
  text(byId("citationsButton"), presentation.citations_appendix ? "Remove citations slide" : "Add citations slide");
  schedulePreflight();
  previewSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const guided = currentWorkflow() === "guided";
  let decisionBrief;
  let topicValue;
  try {
    if (guided) decisionBrief = collectDecisionBrief();
    else {
      topicValue = topic.value.trim();
      if (topicValue.length < 3) {
        setFormError("Add a presentation topic of at least three characters.");
        topic.focus();
        return;
      }
    }
  } catch (error) {
    if (error instanceof Error && error.message === "invalid-guided-brief") return;
    throw error;
  }
  setFormError();
  previewSection.hidden = true;
  progressSection.hidden = false;
  setLoading(true);
  setProgress(18, "Finding the through-line.", "Creating an editable presentation outline…");
  try {
    const result = guided
      ? await post("/api/v1/stories/decision-brief", { brief: decisionBrief, theme: state.theme })
      : await post("/api/content", {
        topic: topicValue,
        slide_count: Number(count.value),
        brief: byId("briefText").value.trim(),
        use_ai: byId("useAi").checked,
        slide_configs: currentConfigs(),
      });
    setProgress(78, "Composing the sequence.", "Turning your brief into a deck you can inspect…");
    window.setTimeout(() => {
      setProgress(100, "Your storyboard is ready.", "Review the sequence, then export a fully editable PowerPoint.");
      renderPreview(result);
    }, 280);
  } catch (error) {
    progressSection.hidden = true;
    setFormError(error instanceof Error ? error.message : "Something went wrong. Please try again.");
    topic.focus();
  } finally {
    setLoading(false);
  }
});

byId("downloadButton").addEventListener("click", async () => {
  if (!state.presentation) return;
  const button = byId("downloadButton");
  button.disabled = true;
  button.querySelector("span").textContent = "Preparing PowerPoint…";
  try {
    const preflight = await runLayoutPreflight();
    if (preflight.findings.length) {
      byId("layoutPreflight").scrollIntoView({ behavior: "smooth", block: "center" });
      throw new Error("Resolve the highlighted layout findings before export. Storyboard Studio will not silently clip the deck.");
    }
    const result = await post("/api/presentations", { presentation: state.presentation });
    const link = document.createElement("a");
    link.href = result.download_url;
    link.download = "storyboard-presentation.pptx";
    document.body.append(link);
    link.click();
    link.remove();
    state.dirty = false;
    text(byId("saveStatus"), "Exported — edits are now saved in this download");
    text(byId("generationNotice"), "Your editable PowerPoint is downloading. The server copy expires after 24 hours.");
  } catch (error) {
    text(byId("generationNotice"), error instanceof Error ? error.message : "The PowerPoint could not be created. Please try again.");
  } finally {
    button.disabled = false;
    button.querySelector("span").textContent = "Export PowerPoint";
  }
});

byId("bundleButton").addEventListener("click", async () => {
  const story = currentStory();
  if (!story) return;
  const button = byId("bundleButton");
  button.disabled = true;
  text(button, "Preparing bundle…");
  try {
    const result = await post("/api/v1/bundles", story);
    const link = document.createElement("a");
    link.href = result.download_url;
    link.download = "storyboard-review-bundle.zip";
    document.body.append(link);
    link.click();
    link.remove();
    text(byId("saveStatus"), "Review bundle exported with story and receipt");
  } catch (error) {
    text(byId("generationNotice"), error instanceof Error ? error.message : "The review bundle could not be created.");
  } finally {
    button.disabled = false;
    text(button, "Export review bundle");
  }
});

byId("undoButton").addEventListener("click", undo);
byId("redoButton").addEventListener("click", redo);
byId("doctorButton").addEventListener("click", runDoctor);
byId("citationsButton").addEventListener("click", () => {
  if (!state.presentation) return;
  const previous = clone(state.presentation);
  state.presentation.citations_appendix = !state.presentation.citations_appendix;
  commitHistory(previous, `${state.presentation.citations_appendix ? "Enabled" : "Disabled"} citations appendix`);
  renderPreview({ presentation: state.presentation, source: state.source });
});
byId("addSlideButton").addEventListener("click", () => {
  if (!state.presentation || state.presentation.slides.length >= 10) return;
  const previous = clone(state.presentation);
  const number = state.presentation.slides.length + 1;
  state.presentation.slides.push({
    slide_number: number,
    title: "New story beat",
    content: "Describe the next useful point in the narrative.",
    layout: "right",
    block: "standard",
    content_block: {
      type: "standard",
      points: [
        { label: "01", title: "First point", description: "Add the context that matters." },
        { label: "02", title: "Second point", description: "Make the trade-off visible." },
        { label: "03", title: "Third point", description: "Name the next action." },
      ],
    },
  });
  commitHistory(previous);
  renderPreview({ presentation: state.presentation, source: state.source });
});

byId("exportOutlineButton").addEventListener("click", () => {
  const story = currentStory();
  if (!story) return;
  const blob = new Blob([JSON.stringify(story, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "storyboard.story.json";
  link.click();
  URL.revokeObjectURL(link.href);
  text(byId("saveStatus"), "Outline downloaded locally");
});

byId("exportMarkdownButton").addEventListener("click", () => {
  const story = currentStory();
  if (!story) return;
  const blob = new Blob([storyToMarkdown(story)], { type: "text/markdown;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "storyboard.story.md";
  link.click();
  URL.revokeObjectURL(link.href);
  text(byId("saveStatus"), "Reviewable Markdown downloaded locally");
});

byId("importOutlineButton").addEventListener("click", () => byId("importOutlineInput").click());
byId("importBrandKitButton").addEventListener("click", () => byId("importBrandKitInput").click());
byId("importSourceMaterialButton").addEventListener("click", () => byId("sourceMaterialInput").click());
byId("mapSourceExcerptButton").addEventListener("click", mapSelectedSourceExcerpt);
byId("sourceMaterialSlide").addEventListener("change", renderSourceMaterialTargets);
["select", "keyup", "mouseup", "touchend"].forEach((eventName) => byId("sourceMaterialText").addEventListener(eventName, updateSourceBoundaryStatus));

byId("sourceMaterialInput").addEventListener("change", async (event) => {
  const file = event.target.files && event.target.files[0];
  if (!file) return;
  try {
    if (!/\.(md|markdown|txt)$/i.test(file.name)) throw new Error("Source material must be one local .md, .markdown, or .txt file.");
    const content = await file.text();
    if (content.length > 20000) throw new Error("Source material is larger than the local 20,000-character review limit.");
    state.sourceMaterialName = safeSourceMaterialName(file.name);
    byId("sourceMaterialText").value = content;
    byId("sourceMaterialLabel").value = file.name.replace(/\.(md|markdown|txt)$/i, "").slice(0, 100);
    updateSourceBoundaryStatus();
    text(byId("sourceMaterialStatus"), "Loaded locally. Select the exact excerpt that supports one claim; the full file will not be embedded.");
  } catch (error) {
    text(byId("sourceMaterialStatus"), error instanceof Error ? error.message : "Source material import failed.");
  }
  event.target.value = "";
});

byId("importBrandKitInput").addEventListener("change", async (event) => {
  const file = event.target.files && event.target.files[0];
  if (!file || !state.presentation) return;
  try {
    const kit = validateBrandKit(JSON.parse(await file.text()));
    const previous = clone(state.presentation);
    state.presentation.brand_kit = kit;
    state.theme = kit.base_theme;
    state.presentation.theme = kit.base_theme;
    const radio = document.querySelector(`input[name=theme][value="${kit.base_theme}"]`);
    if (radio) radio.checked = true;
    document.querySelectorAll(".theme-option").forEach((label) => label.classList.toggle("selected", label.contains(radio)));
    commitHistory(previous, `Applied local brand kit ${kit.name}`);
    renderPreview({ presentation: state.presentation, source: state.source });
    text(byId("saveStatus"), `Local brand kit applied: ${kit.name}`);
  } catch (error) {
    text(byId("saveStatus"), error instanceof Error ? error.message : "Brand-kit import failed");
  }
  event.target.value = "";
});

byId("clearBrandKitButton").addEventListener("click", () => {
  if (!state.presentation || !state.presentation.brand_kit) return;
  const previous = clone(state.presentation);
  delete state.presentation.brand_kit;
  commitHistory(previous, "Removed the local brand kit");
  renderPreview({ presentation: state.presentation, source: state.source });
  text(byId("saveStatus"), "Local brand kit removed");
});

function validateSemanticBlock(block, position, fail, assertKeys) {
  const stringField = (object, key, minimum, maximum, label = key) => {
    if (typeof object[key] !== "string" || object[key].trim().length < minimum || object[key].length > maximum) {
      fail(`${position} ${label} must contain ${minimum}–${maximum} characters.`);
    }
  };
  const arrayField = (object, key, minimum, maximum) => {
    if (!Array.isArray(object[key]) || object[key].length < minimum || object[key].length > maximum) {
      fail(`${position} ${key} must contain ${minimum}–${maximum} items.`);
    }
  };
  if (!block || typeof block !== "object" || Array.isArray(block)) fail(`${position} content_block must be an object.`);
  if (!blockChoices.some(([value]) => value === block.type)) fail(`${position} content_block type is not supported.`);
  if (block.type === "standard") {
    assertKeys(block, ["type", "points"], `${position} standard block`);
    arrayField(block, "points", 1, 4);
    block.points.forEach((point, index) => {
      assertKeys(point, ["label", "title", "description"], `${position} point ${index + 1}`);
      stringField(point, "label", 1, 8);
      stringField(point, "title", 1, 62);
      stringField(point, "description", 1, 120);
    });
  } else if (block.type === "comparison") {
    assertKeys(block, ["type", "sides", "criteria"], `${position} comparison block`);
    arrayField(block, "sides", 2, 2);
    arrayField(block, "criteria", 1, 3);
    block.sides.forEach((side, index) => {
      assertKeys(side, ["title", "summary"], `${position} side ${index + 1}`);
      stringField(side, "title", 1, 70);
      stringField(side, "summary", 1, 180);
    });
    block.criteria.forEach((criterion, index) => {
      assertKeys(criterion, ["label", "left", "right"], `${position} criterion ${index + 1}`);
      stringField(criterion, "label", 1, 60);
      stringField(criterion, "left", 1, 120);
      stringField(criterion, "right", 1, 120);
    });
  } else if (block.type === "decision") {
    assertKeys(block, ["type", "decision", "options", "rationale", "owner"], `${position} decision block`);
    stringField(block, "decision", 1, 180);
    arrayField(block, "options", 2, 3);
    block.options.forEach((option, index) => {
      assertKeys(option, ["title", "description"], `${position} option ${index + 1}`);
      stringField(option, "title", 1, 70);
      stringField(option, "description", 1, 220);
    });
    stringField(block, "rationale", 1, 220);
    stringField(block, "owner", 0, 80);
  } else if (block.type === "timeline") {
    assertKeys(block, ["type", "steps"], `${position} timeline block`);
    arrayField(block, "steps", 2, 4);
    block.steps.forEach((step, index) => {
      assertKeys(step, ["label", "title", "owner"], `${position} step ${index + 1}`);
      stringField(step, "label", 1, 24);
      stringField(step, "title", 1, 80);
      stringField(step, "owner", 0, 80);
    });
  } else if (block.type === "metric") {
    assertKeys(block, ["type", "value", "label", "context", "source"], `${position} metric block`);
    stringField(block, "value", 1, 24);
    stringField(block, "label", 1, 80);
    stringField(block, "context", 1, 220);
    stringField(block, "source", 0, 120);
  } else if (block.type === "process") {
    assertKeys(block, ["type", "steps"], `${position} process block`);
    arrayField(block, "steps", 3, 5);
    block.steps.forEach((step, index) => {
      assertKeys(step, ["title", "description"], `${position} process step ${index + 1}`);
      stringField(step, "title", 1, 70);
      stringField(step, "description", 1, 140);
    });
  } else if (block.type === "quote") {
    assertKeys(block, ["type", "quote", "attribution", "evidence"], `${position} quote block`);
    stringField(block, "quote", 1, 280);
    stringField(block, "attribution", 1, 100);
    stringField(block, "evidence", 0, 180);
  } else if (block.type === "table") {
    assertKeys(block, ["type", "columns", "rows", "accessible_summary"], `${position} table block`);
    arrayField(block, "columns", 2, 4);
    block.columns.forEach((column, index) => {
      if (typeof column !== "string" || !column.trim() || column.length > 60) fail(`${position} column ${index + 1} is invalid.`);
    });
    arrayField(block, "rows", 1, 5);
    block.rows.forEach((row, rowIndex) => {
      assertKeys(row, ["cells"], `${position} row ${rowIndex + 1}`);
      if (!Array.isArray(row.cells) || row.cells.length !== block.columns.length) fail(`${position} row ${rowIndex + 1} must match the column count.`);
      row.cells.forEach((cell, columnIndex) => {
        if (typeof cell !== "string" || !cell.trim() || cell.length > 100) fail(`${position} row ${rowIndex + 1} cell ${columnIndex + 1} is invalid.`);
      });
    });
    stringField(block, "accessible_summary", 1, 300, "accessible summary");
  } else if (block.type === "chart") {
    assertKeys(block, ["type", "chart_type", "asset_id", "category_field", "value_fields", "title", "source_note"], `${position} chart block`);
    if (!["bar", "line", "donut"].includes(block.chart_type)) fail(`${position} chart type is invalid.`);
    stringField(block, "asset_id", 1, 64, "asset id");
    stringField(block, "category_field", 1, 60, "category field");
    arrayField(block, "value_fields", 1, 3);
    block.value_fields.forEach((field, index) => {
      if (typeof field !== "string" || !field.trim() || field.length > 60) fail(`${position} value field ${index + 1} is invalid.`);
    });
    if (new Set(block.value_fields).size !== block.value_fields.length) fail(`${position} chart value fields must be unique.`);
    stringField(block, "title", 1, 100, "chart title");
    stringField(block, "source_note", 1, 180, "source note");
  } else if (block.type === "image") {
    assertKeys(block, ["type", "asset_id", "alt_text", "caption", "fit"], `${position} image block`);
    stringField(block, "asset_id", 1, 64, "asset id");
    stringField(block, "alt_text", 1, 240, "alt text");
    stringField(block, "caption", 0, 160);
    if (!["contain", "cover"].includes(block.fit)) fail(`${position} image fit is invalid.`);
  }
}

function validateBrandKit(value) {
  const fail = (message) => { throw new Error(`Invalid brand kit: ${message}`); };
  if (!value || typeof value !== "object" || Array.isArray(value)) fail("expected a JSON object.");
  const allowed = ["schema_version", "name", "base_theme", "colors", "display_font_fallbacks", "body_font_fallbacks"];
  Object.keys(value).filter((key) => !allowed.includes(key)).forEach((key) => fail(`unsupported field “${key}”.`));
  if (value.schema_version !== "1") fail("schema_version must be 1.");
  if (typeof value.name !== "string" || !value.name.trim() || value.name.length > 60) fail("name must contain 1–60 characters.");
  if (!Object.keys(themes).includes(value.base_theme)) fail("base_theme is not supported.");
  const colorKeys = ["bg", "surface", "surface_alt", "text", "muted", "accent", "accent_soft"];
  if (!value.colors || typeof value.colors !== "object" || Array.isArray(value.colors)) fail("colors must be an object.");
  Object.keys(value.colors).filter((key) => !colorKeys.includes(key)).forEach((key) => fail(`unsupported color “${key}”.`));
  colorKeys.forEach((key) => {
    if (typeof value.colors[key] !== "string" || !/^#?[a-fA-F0-9]{6}$/.test(value.colors[key])) fail(`${key} must be a six-digit RGB color.`);
    value.colors[key] = value.colors[key].replace("#", "").toUpperCase();
  });
  const luminance = (hex) => [0, 2, 4]
    .map((index) => parseInt(hex.slice(index, index + 2), 16) / 255)
    .map((channel) => channel <= .04045 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4)
    .reduce((sum, channel, index) => sum + channel * [.2126, .7152, .0722][index], 0);
  const ratio = (first, second) => {
    const values = [luminance(first), luminance(second)].sort((a, b) => b - a);
    return (values[0] + .05) / (values[1] + .05);
  };
  if (ratio(value.colors.text, value.colors.bg) < 4.5 || ratio(value.colors.muted, value.colors.bg) < 4.5 || ratio(value.colors.text, value.colors.surface) < 4.5 || ratio(value.colors.accent, value.colors.bg) < 3) fail("colors do not meet the shared contrast contract.");
  ["display_font_fallbacks", "body_font_fallbacks"].forEach((key) => {
    const fonts = value[key];
    if (!Array.isArray(fonts) || fonts.length < 2 || fonts.length > 6 || !["serif", "sans-serif", "monospace", "system-ui"].includes(String(fonts.at(-1)).toLowerCase())) fail(`${key} must contain 2–6 local names and end with a generic family.`);
    if (fonts.some((font) => typeof font !== "string" || font.includes("://") || font.length > 80)) fail(`${key} cannot contain URLs or invalid font names.`);
  });
  return value;
}

function validateOutline(value) {
  const fail = (message) => { throw new Error(`Invalid outline: ${message}`); };
  const assertKeys = (object, allowed, label) => {
    Object.keys(object).filter((key) => !allowed.includes(key)).forEach((key) => fail(`${label} contains unsupported field “${key}”.`));
  };
  if (!value || typeof value !== "object" || Array.isArray(value)) fail("expected a JSON object.");
  assertKeys(value, ["title", "subtitle", "theme", "slides", "assets", "brand_kit", "citations_appendix"], "outline");
  if (typeof value.title !== "string" || !value.title.trim() || value.title.length > 90) fail("title must be 1–90 characters.");
  if (value.subtitle !== undefined && (typeof value.subtitle !== "string" || value.subtitle.length > 110)) fail("subtitle must be at most 110 characters.");
  const themesAllowed = ["midnight", "glacier", "ember", "forest", "royal", "sakura"];
  if (value.theme !== undefined && !themesAllowed.includes(value.theme)) fail("theme is not supported.");
  if (value.brand_kit !== undefined && value.brand_kit !== null) value.brand_kit = validateBrandKit(value.brand_kit);
  if (value.citations_appendix !== undefined && typeof value.citations_appendix !== "boolean") fail("citations_appendix must be true or false.");
  if (value.assets !== undefined && (!Array.isArray(value.assets) || value.assets.length > 12)) fail("assets must contain at most 12 items.");
  const assetIds = new Set();
  (value.assets || []).forEach((asset, index) => {
    const label = `asset ${index + 1}`;
    if (!asset || typeof asset !== "object" || Array.isArray(asset)) fail(`${label} must be an object.`);
    assertKeys(asset, ["id", "kind", "path", "sha256", "media_type", "license", "attribution", "alt_text", "source_note"], label);
    if (typeof asset.id !== "string" || !/^[a-z0-9][a-z0-9._-]{0,63}$/.test(asset.id) || assetIds.has(asset.id)) fail(`${label} id is invalid or duplicated.`);
    assetIds.add(asset.id);
    if (!["data", "image"].includes(asset.kind)) fail(`${label} kind is invalid.`);
    if (typeof asset.path !== "string" || !asset.path || asset.path.includes("://") || asset.path.startsWith("/") || asset.path.split("/").includes("..")) fail(`${label} path must be local and relative.`);
    if (typeof asset.sha256 !== "string" || !/^[a-f0-9]{64}$/.test(asset.sha256)) fail(`${label} SHA-256 is invalid.`);
    const media = ["text/csv", "application/json", "image/png", "image/jpeg", "image/svg+xml"];
    if (!media.includes(asset.media_type)) fail(`${label} media type is invalid.`);
    if (typeof asset.license !== "string" || !asset.license.trim() || asset.license.length > 100) fail(`${label} license is required.`);
    if (typeof asset.attribution !== "string" || !asset.attribution.trim() || asset.attribution.length > 180) fail(`${label} attribution is required.`);
    if (asset.kind === "data" && (typeof asset.source_note !== "string" || !asset.source_note.trim() || asset.source_note.length > 180)) fail(`${label} data source note is required.`);
    if (asset.kind === "image" && (typeof asset.alt_text !== "string" || !asset.alt_text.trim() || asset.alt_text.length > 240)) fail(`${label} image alt text is required.`);
  });
  if (!Array.isArray(value.slides) || value.slides.length < 3 || value.slides.length > 10) fail("slides must contain 3–10 items.");
  const layouts = ["left", "right", "focus"];
  const blocks = blockChoices.map(([value]) => value);
  value.slides.forEach((slide, index) => {
    const position = `slide ${index + 1}`;
    if (!slide || typeof slide !== "object" || Array.isArray(slide)) fail(`${position} must be an object.`);
    assertKeys(slide, ["slide_number", "title", "content", "bullet_points", "layout", "block", "content_block", "sources", "speaker_notes"], position);
    if (typeof slide.title !== "string" || !slide.title.trim() || slide.title.length > 68) fail(`${position} title must be 1–68 characters.`);
    if (typeof slide.content !== "string" || !slide.content.trim() || slide.content.length > 220) fail(`${position} content must be 1–220 characters.`);
    if (!layouts.includes(slide.layout || "right")) fail(`${position} layout is not supported.`);
    if (!blocks.includes(slide.block || "standard")) fail(`${position} block is not supported.`);
    if (slide.content_block) {
      validateSemanticBlock(slide.content_block, position, fail, assertKeys);
      if (slide.content_block.type !== (slide.block || "standard")) fail(`${position} block must match content_block.type.`);
      if (["chart", "image"].includes(slide.content_block.type) && !assetIds.has(slide.content_block.asset_id)) fail(`${position} references an unknown local asset.`);
    } else if (!Array.isArray(slide.bullet_points) || slide.bullet_points.length !== 3) {
      fail(`${position} legacy slides must contain exactly 3 bullet points.`);
    }
    if (slide.bullet_points !== undefined && (!Array.isArray(slide.bullet_points) || slide.bullet_points.length > 3)) fail(`${position} bullet_points must contain at most 3 items.`);
    (slide.bullet_points || []).forEach((bullet, bulletIndex) => {
      if (!bullet || typeof bullet !== "object") fail(`${position} bullet ${bulletIndex + 1} is invalid.`);
      assertKeys(bullet, ["label", "title", "description"], `${position} bullet ${bulletIndex + 1}`);
      if (typeof bullet.label !== "string" || !bullet.label.trim() || bullet.label.length > 8) fail(`${position} bullet ${bulletIndex + 1} label is invalid.`);
      if (typeof bullet.title !== "string" || !bullet.title.trim() || bullet.title.length > 62) fail(`${position} bullet ${bulletIndex + 1} title is invalid.`);
      if (typeof bullet.description !== "string" || !bullet.description.trim() || bullet.description.length > 120) fail(`${position} bullet ${bulletIndex + 1} description is invalid.`);
    });
    if (slide.sources !== undefined && (!Array.isArray(slide.sources) || slide.sources.length > 6)) fail(`${position} sources must contain at most 6 items.`);
    (slide.sources || []).forEach((source, sourceIndex) => {
      if (!source || typeof source !== "object" || typeof source.label !== "string" || !source.label.trim() || source.label.length > 100) fail(`${position} source ${sourceIndex + 1} label is invalid.`);
      assertKeys(source, ["label", "evidence", "owner", "url", "local_reference", "checked_date", "license", "review_status", "claim_ids"], `${position} source ${sourceIndex + 1}`);
      if (source.evidence !== undefined && (typeof source.evidence !== "string" || source.evidence.length > 300)) fail(`${position} source ${sourceIndex + 1} evidence is invalid.`);
      if (source.owner !== undefined && (typeof source.owner !== "string" || source.owner.length > 80)) fail(`${position} source ${sourceIndex + 1} owner is invalid.`);
      if (source.url !== undefined && source.url) {
        let parsed;
        try { parsed = new URL(source.url); } catch (error) { fail(`${position} source ${sourceIndex + 1} URL is invalid.`); }
        const hostname = parsed.hostname.toLowerCase();
        if (!["http:", "https:"].includes(parsed.protocol) || parsed.username || parsed.password || hostname === "localhost" || hostname.endsWith(".local") || /^(127\.|10\.|192\.168\.|169\.254\.|172\.(1[6-9]|2\d|3[01])\.)/.test(hostname)) fail(`${position} source ${sourceIndex + 1} URL must be a public HTTP(S) locator without credentials.`);
      }
      if (source.local_reference !== undefined && source.local_reference && (typeof source.local_reference !== "string" || source.local_reference.includes("://") || source.local_reference.includes("\\") || source.local_reference.startsWith("/") || source.local_reference.split("#")[0].split("/").includes(".."))) fail(`${position} source ${sourceIndex + 1} local reference is invalid.`);
      if (source.checked_date !== undefined && source.checked_date !== null && (typeof source.checked_date !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(source.checked_date))) fail(`${position} source ${sourceIndex + 1} checked date is invalid.`);
      if (source.license !== undefined && (typeof source.license !== "string" || source.license.length > 100)) fail(`${position} source ${sourceIndex + 1} license is invalid.`);
      const reviewStatus = source.review_status || "unresolved";
      if (!["unresolved", "author-checked"].includes(reviewStatus)) fail(`${position} source ${sourceIndex + 1} review status is invalid.`);
      if (source.claim_ids !== undefined && (!Array.isArray(source.claim_ids) || source.claim_ids.length > 12 || new Set(source.claim_ids).size !== source.claim_ids.length || source.claim_ids.some((claimId) => typeof claimId !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(claimId) || claimId.length > 80))) fail(`${position} source ${sourceIndex + 1} claim ids are invalid.`);
      if (reviewStatus === "author-checked" && (!source.owner || !source.checked_date || (!source.url && !source.local_reference))) fail(`${position} source ${sourceIndex + 1} author-checked evidence needs an owner, checked date, and URL or local reference.`);
    });
    if (slide.speaker_notes !== undefined && (typeof slide.speaker_notes !== "string" || slide.speaker_notes.length > 1200)) fail(`${position} speaker notes are invalid.`);
  });
  return value;
}

function validateStory(value) {
  const allowed = ["schema_version", "kind", "template", "presentation", "decision_brief", "planner", "provider_warning", "author_edits", "finding_dispositions"];
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new Error("Invalid story: expected a JSON object.");
  Object.keys(value).filter((key) => !allowed.includes(key)).forEach((key) => { throw new Error(`Invalid story: unsupported field “${key}”.`); });
  if (value.schema_version !== "2") throw new Error("Invalid story: schema_version must be 2. Use storyboard migrate for v1 outlines.");
  if (!["decision-brief", "freeform-outline"].includes(value.kind)) throw new Error("Invalid story: unsupported story kind.");
  value.presentation = validateOutline(value.presentation);
  value.finding_dispositions = Array.isArray(value.finding_dispositions) ? value.finding_dispositions : [];
  value.author_edits = Array.isArray(value.author_edits) ? value.author_edits : [];
  return value;
}

byId("importOutlineInput").addEventListener("change", async (event) => {
  const file = event.target.files && event.target.files[0];
  if (!file) return;
  try {
    const contents = await file.text();
    const markdown = /\.(md|markdown)$/i.test(file.name);
    const raw = markdown ? null : JSON.parse(contents);
    const isStory = raw && raw.schema_version === "2";
    const parsedStory = markdown ? markdownToStory(contents) : (isStory ? validateStory(raw) : null);
    const parsed = parsedStory ? parsedStory.presentation : validateOutline(raw);
    const previous = clone(state.presentation);
    state.story = parsedStory || {
      schema_version: "2",
      kind: "freeform-outline",
      template: "freeform",
      presentation: parsed,
      decision_brief: null,
      planner: "imported",
      provider_warning: "Imported explicitly from a v1 freeform outline; decision fields were not inferred.",
      author_edits: [],
      finding_dispositions: [],
    };
    state.presentation = parsed;
    renumberSlides();
    commitHistory(previous);
    renderPreview({ presentation: state.presentation, story: state.story, source: "local" });
    text(byId("saveStatus"), markdown ? "Markdown story imported locally" : (parsedStory ? "Story imported locally" : "Legacy v1 outline imported as freeform; decision fields were not inferred"));
  } catch (error) {
    text(byId("saveStatus"), error instanceof Error ? error.message : "Outline import failed");
  }
  event.target.value = "";
});

byId("localModeButton").addEventListener("click", () => {
  byId("useAi").checked = false;
  text(byId("localModeButton"), "Local planner selected");
});

window.addEventListener("beforeunload", (event) => {
  if (!state.dirty) return;
  event.preventDefault();
  event.returnValue = "You have unsaved storyboard edits.";
});

byId("reviseButton").addEventListener("click", () => {
  previewSection.hidden = true;
  byId("brief").scrollIntoView({ behavior: "smooth", block: "start" });
  topic.focus();
});

byId("demoButton").addEventListener("click", () => {
  const guided = document.querySelector('input[name="workflow"][value="guided"]');
  guided.checked = true;
  setWorkflowMode();
  byId("decision").value = "Choose the onboarding pilot for the next release";
  byId("currentContext").value = "New customers receive inconsistent guidance after the sales handoff, and the team needs one bounded pilot before expanding the workflow.";
  byId("audience").value = "Product and customer-success leaders";
  byId("desiredOutcome").value = "Approve one measurable first-30-day onboarding experience";
  byId("constraints").value = "No new platform\nOne product team\nSix-week pilot";
  byId("tradeOffs").value = "Reach versus learning depth\nSpeed versus automation";
  byId("option1Title").value = "Concierge pilot";
  byId("option1Description").value = "A human-led cohort using the current product and a shared checklist.";
  byId("option2Title").value = "In-product pilot";
  byId("option2Description").value = "A guided workflow implemented inside the current product experience.";
  byId("evidenceLabel").value = "Support handoff review";
  byId("evidenceText").value = "Author-owned synthesis from recent customer handoffs.";
  byId("evidenceOwner").value = "";
  byId("decisionOwner").value = "Onboarding lead";
  byId("nextStep").value = "Run a five-customer concierge pilot and review the evidence";
  byId("reviewDate").value = "2026-09-30";
  topic.value = "A practical plan to make remote onboarding feel human";
  byId("briefText").value = "Align product and customer-success leaders on a first 30-day experience.";
  text(byId("topic-count"), `${topic.value.length} / 240`);
  byId("decision").focus();
  byId("brief").scrollIntoView({ behavior: "smooth", block: "start" });
});

topic.addEventListener("input", () => text(byId("topic-count"), `${topic.value.length} / 240`));
count.addEventListener("change", buildSlideConfigs);
byId("storyControls").addEventListener("toggle", (event) => { if (event.currentTarget.open) buildSlideConfigs(); });
document.querySelectorAll("input[name=theme]").forEach((input) => {
  input.addEventListener("change", () => {
    state.theme = input.value;
    document.querySelectorAll(".theme-option").forEach((label) => label.classList.toggle("selected", label.contains(input)));
    if (state.presentation) renderPreview({ presentation: state.presentation, source: state.source });
  });
});
document.querySelectorAll("input[name=workflow]").forEach((input) => input.addEventListener("change", setWorkflowMode));

byId("canvasViewButton").addEventListener("click", () => setPreviewMode("canvas"));
byId("outlineViewButton").addEventListener("click", () => setPreviewMode("outline"));
byId("zoomOutButton").addEventListener("click", () => setZoom(state.zoom - 25));
byId("zoomInButton").addEventListener("click", () => setZoom(state.zoom + 25));
window.addEventListener("resize", () => {
  if (state.previewModeExplicit) return;
  applyPreviewMode(window.innerWidth <= 560 ? "outline" : "canvas");
});

setWorkflowMode();
buildSlideConfigs();
applyPreviewMode();
void initializeLayoutContract();
