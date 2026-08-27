"use strict";

const state = { presentation: null, story: null, report: null, theme: "midnight", configs: new Map(), history: [], future: [], dirty: false, source: "local" };
const themes = {
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
    blockChoices.forEach(([value, label]) => {
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
  };
  return blocks[requestedType] || blocks.standard;
}

function ensureContentBlock(slide) {
  if (!slide.content_block || !slide.content_block.type) {
    slide.content_block = contentBlockFor(slide);
  }
  return slide.content_block;
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
  }
  card.append(editor);
  const fallback = create("details", "semantic-fallback");
  fallback.append(create("summary", "", "Plain-text block"), create("p", "", semanticPlainText(block)));
  card.append(fallback);
}

function addPreviewSlide(container, slide, index, isTitle = false) {
  const colors = themes[state.theme] || themes.midnight;
  const card = create("article", `slide-preview${isTitle ? " title-preview" : ""}`);
  card.style.setProperty("--preview-bg", colors.bg);
  card.style.setProperty("--preview-text", colors.text);
  card.style.setProperty("--preview-muted", colors.muted);
  card.style.setProperty("--preview-accent", colors.accent);
  card.style.setProperty("--preview-surface", colors.surface);
  card.append(create("span", "preview-index", isTitle ? "STORYBOARD / TITLE" : `STORYBOARD / ${String(index).padStart(2, "0")}`));
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
    const source = create("input", "preview-editable preview-source-edit");
    source.value = slide.sources && slide.sources[0] ? slide.sources[0].label || "" : "";
    source.placeholder = "Source / evidence label (optional)";
    source.setAttribute("aria-label", `Source or evidence for slide ${index}`);
    source.addEventListener("change", () => updateSlideSource(index - 1, "label", source.value));
    card.append(source);
    const owner = create("input", "preview-editable preview-source-edit");
    owner.value = slide.sources && slide.sources[0] ? slide.sources[0].owner || "" : "";
    owner.placeholder = "Evidence owner (optional)";
    owner.setAttribute("aria-label", `Evidence owner for slide ${index}`);
    owner.addEventListener("change", () => updateSlideSource(index - 1, "owner", owner.value));
    card.append(owner);
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
    blockChoices.forEach(([value, label]) => {
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

function updateSlideSource(index, field, value) {
  const previous = clone(state.presentation);
  const slide = state.presentation.slides[index];
  slide.sources = slide.sources && slide.sources.length ? slide.sources : [{ label: "Author source", evidence: "", owner: "" }];
  slide.sources[0][field] = value;
  if (!slide.sources[0].label.trim() && !slide.sources[0].evidence.trim() && !slide.sources[0].owner.trim()) slide.sources = [];
  commitHistory(previous, `Changed evidence ${field} on slide ${index + 1}`);
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
    const label = finding.path.includes("sources") ? `Evidence owner for slide ${finding.slide_number}` : `Slide ${finding.slide_number} title`;
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
  text(byId("doctorSummary"), `${summary.errors} errors · ${summary.warnings} warnings · ${summary.information} notes · ${summary.open_findings ?? report.findings.length} open. Structural review only; factual truth is not verified.`);
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
  addPreviewSlide(deck, { title: presentation.title, subtitle: presentation.subtitle }, 0, true);
  presentation.slides.forEach((slide, index) => addPreviewSlide(deck, slide, index + 1));
  renderStoryMap();
  const saveStatus = byId("saveStatus");
  if (saveStatus && !state.dirty) text(saveStatus, "No edits yet");
  previewSection.hidden = false;
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

byId("importOutlineButton").addEventListener("click", () => byId("importOutlineInput").click());

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
  }
}

function validateOutline(value) {
  const fail = (message) => { throw new Error(`Invalid outline: ${message}`); };
  const assertKeys = (object, allowed, label) => {
    Object.keys(object).filter((key) => !allowed.includes(key)).forEach((key) => fail(`${label} contains unsupported field “${key}”.`));
  };
  if (!value || typeof value !== "object" || Array.isArray(value)) fail("expected a JSON object.");
  assertKeys(value, ["title", "subtitle", "theme", "slides"], "outline");
  if (typeof value.title !== "string" || !value.title.trim() || value.title.length > 90) fail("title must be 1–90 characters.");
  if (value.subtitle !== undefined && (typeof value.subtitle !== "string" || value.subtitle.length > 110)) fail("subtitle must be at most 110 characters.");
  const themesAllowed = ["midnight", "glacier", "ember", "forest", "royal", "sakura"];
  if (value.theme !== undefined && !themesAllowed.includes(value.theme)) fail("theme is not supported.");
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
      assertKeys(source, ["label", "evidence", "owner"], `${position} source ${sourceIndex + 1}`);
      if (source.evidence !== undefined && (typeof source.evidence !== "string" || source.evidence.length > 300)) fail(`${position} source ${sourceIndex + 1} evidence is invalid.`);
      if (source.owner !== undefined && (typeof source.owner !== "string" || source.owner.length > 80)) fail(`${position} source ${sourceIndex + 1} owner is invalid.`);
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
    const raw = JSON.parse(await file.text());
    const isStory = raw && raw.schema_version === "2";
    const parsedStory = isStory ? validateStory(raw) : null;
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
    text(byId("saveStatus"), parsedStory ? "Story imported locally" : "Legacy v1 outline imported as freeform; decision fields were not inferred");
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
  });
});
document.querySelectorAll("input[name=workflow]").forEach((input) => input.addEventListener("change", setWorkflowMode));

setWorkflowMode();
buildSlideConfigs();
