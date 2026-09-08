"use strict";

const StoryboardValidation = (() => {
  let readThemes = () => ({});
  let readBlockChoices = () => [];

  function configure({ themes, blockChoices }) {
    readThemes = typeof themes === "function" ? themes : () => themes;
    readBlockChoices = typeof blockChoices === "function" ? blockChoices : () => blockChoices;
  }

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
  if (!readBlockChoices().some(([value]) => value === block.type)) fail(`${position} content_block type is not supported.`);
  if (block.type === "standard") {
    assertKeys(block, ["type", "points"], `${position} standard block`);
    arrayField(block, "points", 1, 4);
    block.points.forEach((point, index) => {
      assertKeys(point, ["label", "title", "description"], `${position} point ${index + 1}`);
      stringField(point, "label", 1, 8);
      stringField(point, "title", 1, 2000);
      stringField(point, "description", 1, 2000);
    });
  } else if (block.type === "comparison") {
    assertKeys(block, ["type", "sides", "criteria"], `${position} comparison block`);
    arrayField(block, "sides", 2, 2);
    arrayField(block, "criteria", 1, 3);
    block.sides.forEach((side, index) => {
      assertKeys(side, ["title", "summary"], `${position} side ${index + 1}`);
      stringField(side, "title", 1, 2000);
      stringField(side, "summary", 1, 2000);
    });
    block.criteria.forEach((criterion, index) => {
      assertKeys(criterion, ["label", "left", "right"], `${position} criterion ${index + 1}`);
      stringField(criterion, "label", 1, 2000);
      stringField(criterion, "left", 1, 2000);
      stringField(criterion, "right", 1, 2000);
    });
  } else if (block.type === "decision") {
    assertKeys(block, ["type", "decision", "options", "rationale", "owner"], `${position} decision block`);
    stringField(block, "decision", 1, 2000);
    arrayField(block, "options", 2, 3);
    block.options.forEach((option, index) => {
      assertKeys(option, ["title", "description"], `${position} option ${index + 1}`);
      stringField(option, "title", 1, 2000);
      stringField(option, "description", 1, 2000);
    });
    stringField(block, "rationale", 1, 2000);
    stringField(block, "owner", 0, 80);
  } else if (block.type === "timeline") {
    assertKeys(block, ["type", "steps"], `${position} timeline block`);
    arrayField(block, "steps", 2, 4);
    block.steps.forEach((step, index) => {
      assertKeys(step, ["label", "title", "owner"], `${position} step ${index + 1}`);
      stringField(step, "label", 1, 24);
      stringField(step, "title", 1, 2000);
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
  if (!Object.keys(readThemes()).includes(value.base_theme)) fail("base_theme is not supported.");
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
  if (typeof value.title !== "string" || !value.title.trim() || value.title.length > 2000) fail("title must be 1–2000 characters.");
  if (value.subtitle !== undefined && (typeof value.subtitle !== "string" || value.subtitle.length > 2000)) fail("subtitle must be at most 2000 characters.");
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
  const blocks = readBlockChoices().map(([value]) => value);
  value.slides.forEach((slide, index) => {
    const position = `slide ${index + 1}`;
    if (!slide || typeof slide !== "object" || Array.isArray(slide)) fail(`${position} must be an object.`);
    assertKeys(slide, ["slide_number", "title", "content", "bullet_points", "layout", "block", "content_block", "sources", "speaker_notes"], position);
    if (typeof slide.title !== "string" || !slide.title.trim() || slide.title.length > 2000) fail(`${position} title must be 1–2000 characters.`);
    if (typeof slide.content !== "string" || !slide.content.trim() || slide.content.length > 2000) fail(`${position} content must be 1–2000 characters.`);
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
      if (typeof bullet.title !== "string" || !bullet.title.trim() || bullet.title.length > 2000) fail(`${position} bullet ${bulletIndex + 1} title is invalid.`);
      if (typeof bullet.description !== "string" || !bullet.description.trim() || bullet.description.length > 2000) fail(`${position} bullet ${bulletIndex + 1} description is invalid.`);
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


  return { configure, validateSemanticBlock, validateBrandKit, validateOutline, validateStory };
})();

