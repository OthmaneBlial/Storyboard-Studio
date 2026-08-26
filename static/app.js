"use strict";

const state = { presentation: null, theme: "midnight", configs: new Map(), history: [], future: [], dirty: false, source: "local" };
const themes = {
  midnight: { bg: "#101425", text: "#f7f4ee", muted: "#b8c0d6", accent: "#e5b560", surface: "#1b2136" },
  glacier: { bg: "#f4f8f8", text: "#123544", muted: "#55727a", accent: "#0a7c86", surface: "#e4eff0" },
  ember: { bg: "#25120f", text: "#fff5e7", muted: "#d6b9a8", accent: "#f08a4b", surface: "#38201a" },
  forest: { bg: "#f1f5ee", text: "#1d3829", muted: "#577060", accent: "#438360", surface: "#e0eadd" },
  royal: { bg: "#17151b", text: "#f5ecd8", muted: "#c7b99a", accent: "#c79c54", surface: "#28242d" },
  sakura: { bg: "#fcf4f4", text: "#4d2736", muted: "#846274", accent: "#be526d", surface: "#f7e5e7" },
};

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

function markDirty() {
  state.dirty = true;
  const status = byId("saveStatus");
  if (status) text(status, "Unsaved storyboard edits");
}

function commitHistory(previous) {
  state.history.push(clone(previous));
  if (state.history.length > 50) state.history.shift();
  state.future = [];
  markDirty();
}

function setPath(path, value) {
  const previous = clone(state.presentation);
  let target = state.presentation;
  path.slice(0, -1).forEach((key) => { target = target[key]; });
  target[path[path.length - 1]] = value;
  commitHistory(previous);
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
    [["standard", "Standard frame"], ["comparison", "Comparison"], ["decision", "Decision"], ["timeline", "Timeline"], ["metric", "Metric"]].forEach(([value, label]) => {
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
  submit.querySelector("span").textContent = loading ? "Building your story…" : "Build my storyboard";
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

function addPreviewSlide(container, slide, index, isTitle = false) {
  const colors = themes[state.theme] || themes.midnight;
  const card = create("article", `slide-preview${isTitle ? " title-preview" : ""}`);
  card.style.setProperty("--preview-bg", colors.bg);
  card.style.setProperty("--preview-text", colors.text);
  card.style.setProperty("--preview-muted", colors.muted);
  card.style.setProperty("--preview-accent", colors.accent);
  card.style.setProperty("--preview-surface", colors.surface);
  card.append(create("span", "preview-index", isTitle ? "STORYBOARD / TITLE" : `STORYBOARD / ${String(index).padStart(2, "0")}`));
  const title = create(isTitle ? "input" : "input", "preview-editable preview-title-edit");
  title.value = slide.title || "";
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
    const list = create("ul");
    (slide.bullet_points || []).slice(0, 3).forEach((point, bulletIndex) => {
      const item = create("li");
      const input = create("input", "preview-editable preview-bullet-edit");
      input.value = point.title || "";
      input.setAttribute("aria-label", `Slide ${index} point ${bulletIndex + 1}`);
      input.addEventListener("change", () => setPath(["slides", index - 1, "bullet_points", bulletIndex, "title"], input.value));
      item.append(input);
      list.append(item);
    });
    card.append(list);
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
    [["standard", "Standard"], ["comparison", "Comparison"], ["decision", "Decision"], ["timeline", "Timeline"], ["metric", "Metric"]].forEach(([value, label]) => {
      const option = create("option", "", label);
      option.value = value;
      option.selected = value === (slide.block || "standard");
      block.append(option);
    });
    block.addEventListener("change", () => setPath(["slides", index - 1, "block"], block.value));
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
  commitHistory(previous);
  renderPreview({ presentation: state.presentation, source: state.source });
}

function duplicateSlide(index) {
  if (state.presentation.slides.length >= 10) return;
  const previous = clone(state.presentation);
  state.presentation.slides.splice(index + 1, 0, clone(state.presentation.slides[index]));
  renumberSlides();
  commitHistory(previous);
  renderPreview({ presentation: state.presentation, source: state.source });
}

function deleteSlide(index) {
  if (state.presentation.slides.length <= 3) return;
  const previous = clone(state.presentation);
  state.presentation.slides.splice(index, 1);
  renumberSlides();
  commitHistory(previous);
  renderPreview({ presentation: state.presentation, source: state.source });
}

function updateSlideSource(index, field, value) {
  const previous = clone(state.presentation);
  const slide = state.presentation.slides[index];
  slide.sources = slide.sources && slide.sources.length ? slide.sources : [{ label: "Author source", evidence: "", owner: "" }];
  slide.sources[0][field] = value;
  if (!slide.sources[0].label.trim() && !slide.sources[0].evidence.trim() && !slide.sources[0].owner.trim()) slide.sources = [];
  commitHistory(previous);
}

function renderPreview(result) {
  const presentation = result.presentation;
  const isNewPresentation = state.presentation !== presentation;
  if (isNewPresentation) {
    state.history = [];
    state.future = [];
    state.dirty = false;
  }
  state.presentation = presentation;
  state.source = result.source || state.source;
  presentation.theme = state.theme;
  text(byId("previewTitle"), presentation.title);
  text(byId("previewSubtitle"), presentation.subtitle);
  text(byId("previewSource"), result.source === "gemini" ? "GEMINI-ASSISTED OUTLINE" : "LOCAL EDITABLE OUTLINE");
  const notice = byId("generationNotice");
  const provider = result.source === "gemini" ? "Gemini-assisted draft" : "Deterministic local draft";
  text(notice, result.warning || `${provider}. Verify unsourced claims and add evidence before sharing. Your export expires from this computer after 24 hours.`);
  notice.hidden = false;
  const deck = byId("deckPreview");
  deck.replaceChildren();
  addPreviewSlide(deck, { title: presentation.title, subtitle: presentation.subtitle }, 0, true);
  presentation.slides.forEach((slide, index) => addPreviewSlide(deck, slide, index + 1));
  const saveStatus = byId("saveStatus");
  if (saveStatus && !state.dirty) text(saveStatus, "No edits yet");
  previewSection.hidden = false;
  previewSection.scrollIntoView({ behavior: "smooth", block: "start" });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const topicValue = topic.value.trim();
  if (topicValue.length < 3) {
    setFormError("Add a presentation topic of at least three characters.");
    topic.focus();
    return;
  }
  setFormError();
  previewSection.hidden = true;
  progressSection.hidden = false;
  setLoading(true);
  setProgress(18, "Finding the through-line.", "Creating an editable presentation outline…");
  try {
    const result = await post("/api/content", {
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

byId("undoButton").addEventListener("click", undo);
byId("redoButton").addEventListener("click", redo);
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
    bullet_points: [
      { label: "01", title: "First point", description: "Add the context that matters." },
      { label: "02", title: "Second point", description: "Make the trade-off visible." },
      { label: "03", title: "Third point", description: "Name the next action." },
    ],
  });
  commitHistory(previous);
  renderPreview({ presentation: state.presentation, source: state.source });
});

byId("exportOutlineButton").addEventListener("click", () => {
  if (!state.presentation) return;
  const blob = new Blob([JSON.stringify(state.presentation, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "storyboard-outline.json";
  link.click();
  URL.revokeObjectURL(link.href);
  text(byId("saveStatus"), "Outline downloaded locally");
});

byId("importOutlineButton").addEventListener("click", () => byId("importOutlineInput").click());

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
  const blocks = ["standard", "comparison", "decision", "timeline", "metric"];
  value.slides.forEach((slide, index) => {
    const position = `slide ${index + 1}`;
    if (!slide || typeof slide !== "object" || Array.isArray(slide)) fail(`${position} must be an object.`);
    assertKeys(slide, ["slide_number", "title", "content", "bullet_points", "layout", "block", "sources", "speaker_notes"], position);
    if (typeof slide.title !== "string" || !slide.title.trim() || slide.title.length > 68) fail(`${position} title must be 1–68 characters.`);
    if (typeof slide.content !== "string" || !slide.content.trim() || slide.content.length > 220) fail(`${position} content must be 1–220 characters.`);
    if (!layouts.includes(slide.layout || "right")) fail(`${position} layout is not supported.`);
    if (!blocks.includes(slide.block || "standard")) fail(`${position} block is not supported.`);
    if (!Array.isArray(slide.bullet_points) || slide.bullet_points.length !== 3) fail(`${position} must contain exactly 3 bullet points.`);
    slide.bullet_points.forEach((bullet, bulletIndex) => {
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

byId("importOutlineInput").addEventListener("change", async (event) => {
  const file = event.target.files && event.target.files[0];
  if (!file) return;
  try {
    const parsed = validateOutline(JSON.parse(await file.text()));
    const previous = clone(state.presentation);
    state.presentation = parsed;
    renumberSlides();
    commitHistory(previous);
    renderPreview({ presentation: state.presentation, source: "local" });
    text(byId("saveStatus"), "Outline imported locally");
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
  topic.value = "A practical plan to make remote onboarding feel human";
  byId("briefText").value = "Align product and customer-success leaders on a first 30-day experience.";
  text(byId("topic-count"), `${topic.value.length} / 240`);
  topic.focus();
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

buildSlideConfigs();
