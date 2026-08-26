"use strict";

const state = { presentation: null, theme: "midnight", configs: new Map() };
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
  card.append(create("h3", "", slide.title));
  card.append(create("p", "", slide.content || slide.subtitle));
  if (!isTitle) {
    const list = create("ul");
    (slide.bullet_points || []).slice(0, 3).forEach((point) => list.append(create("li", "", point.title)));
    card.append(list);
  }
  container.append(card);
}

function renderPreview(result) {
  const presentation = result.presentation;
  state.presentation = presentation;
  presentation.theme = state.theme;
  text(byId("previewTitle"), presentation.title);
  text(byId("previewSubtitle"), presentation.subtitle);
  text(byId("previewSource"), result.source === "gemini" ? "GEMINI-ASSISTED OUTLINE" : "LOCAL EDITABLE OUTLINE");
  const notice = byId("generationNotice");
  text(notice, result.warning || "Review the story here, then download an editable .pptx. Your export expires from this computer after 24 hours.");
  notice.hidden = false;
  const deck = byId("deckPreview");
  deck.replaceChildren();
  addPreviewSlide(deck, { title: presentation.title, subtitle: presentation.subtitle }, 0, true);
  presentation.slides.forEach((slide, index) => addPreviewSlide(deck, slide, index + 1));
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
    text(byId("generationNotice"), "Your editable PowerPoint is downloading. The server copy expires after 24 hours.");
  } catch (error) {
    text(byId("generationNotice"), error instanceof Error ? error.message : "The PowerPoint could not be created. Please try again.");
  } finally {
    button.disabled = false;
    button.querySelector("span").textContent = "Export PowerPoint";
  }
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
