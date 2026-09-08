"use strict";

// Explicit asset bytes stay in this tab. No filesystem probing or browser storage.
const PortableProjects = (() => {
  const bytesByHash = new Map();
  const media = {csv: "text/csv", json: "application/json", png: "image/png", jpg: "image/jpeg", jpeg: "image/jpeg", svg: "image/svg+xml"};
  function retain(project) {
    const additions = new Map();
    for (const asset of project.story.presentation.assets || []) {
      const bytes = project.files[asset.path];
      if (bytes !== undefined) additions.set(asset.sha256, bytes);
    }
    const all = new Map([...bytesByHash, ...additions]);
    if ([...all.values()].reduce((sum, value) => sum + value.length, 0) > 21_333_360) {
      throw new Error("This tab's asset history reached 16 MB. Save your project, then reopen it in a fresh tab.");
    }
    additions.forEach((value, key) => bytesByHash.set(key, value));
  }
  function envelope(story, extra = new Map()) {
    const files = {};
    for (const asset of story.presentation.assets || []) {
      const bytes = extra.get(asset.sha256) ?? bytesByHash.get(asset.sha256);
      if (bytes === undefined) throw new Error(`Missing local asset ${asset.path}. Open a portable project ZIP containing its files; JSON alone contains references.`);
      files[asset.path] = bytes;
    }
    if (Object.values(files).reduce((sum, value) => sum + value.length, 0) > 5_333_360) throw new Error("Keep project assets below 4 MB combined.");
    return {schema_version: "1", story, files, include_sources: true};
  }
  async function selectedFile(file, metadata) {
    if (!file || file.size > 4_000_000) throw new Error("Select one CSV, JSON, PNG, JPEG or SVG file below 4 MB.");
    const extension = file.name.split(".").pop().toLowerCase();
    if (!media[extension]) throw new Error("Supported assets: CSV, JSON, PNG, JPEG and SVG.");
    const raw = new Uint8Array(await file.arrayBuffer());
    const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", raw));
    const sha256 = [...digest].map(value => value.toString(16).padStart(2, "0")).join("");
    let binary = "";
    for (let offset = 0; offset < raw.length; offset += 8192) binary += String.fromCharCode(...raw.subarray(offset, offset + 8192));
    const id = "asset-" + sha256.slice(0, 20);
    const image = media[extension].startsWith("image/");
    return {asset: {id, kind: image ? "image" : "data", path: `assets/${id}.${extension}`, sha256,
      media_type: media[extension], license: metadata.license, attribution: metadata.attribution,
      alt_text: image ? metadata.description : "", source_note: image ? "" : metadata.description}, bytes: btoa(binary)};
  }
  async function open(file) {
    if (file.size > 8_000_000) throw new Error("Project ZIP must be below 8 MB.");
    const response = await fetch("/api/v1/projects/open", {method: "POST", headers: {"Content-Type": "application/zip"}, body: file});
    const result = await response.json();
    if (!response.ok) throw new Error(typeof result.detail === "string" ? result.detail : "The project archive could not be opened.");
    return result;
  }
  return {retain, envelope, selectedFile, open};
})();
