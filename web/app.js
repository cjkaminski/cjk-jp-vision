"use strict";

const $ = (id) => document.getElementById(id);
const fileInput = $("file");
const preview = $("preview");
const goBtn = $("go");
const statusEl = $("status");
const resultEl = $("result");

let selectedFile = null;

// --- Populate backend dropdowns from /health so the UI reflects what's
//     actually installed, and you can switch engines to compare. ---
async function loadBackends() {
  try {
    const r = await fetch("/health");
    const h = await r.json();
    fillSelect($("ocr"), h.ocr_backends);
    fillSelect($("analysis"), h.analysis_backends);
  } catch (e) {
    showStatus("Could not reach server /health. Is it running?", true);
  }
}

function fillSelect(sel, backends) {
  sel.innerHTML = "";
  const auto = document.createElement("option");
  auto.value = "auto";
  auto.textContent = "auto (best available)";
  sel.appendChild(auto);
  for (const [name, ok] of Object.entries(backends)) {
    const opt = document.createElement("option");
    opt.value = name;
    opt.textContent = ok ? name : `${name} (unavailable)`;
    opt.disabled = !ok;
    sel.appendChild(opt);
  }
}

// --- Capture ---
fileInput.addEventListener("change", () => {
  const f = fileInput.files[0];
  if (!f) return;
  selectedFile = f;
  preview.src = URL.createObjectURL(f);
  preview.hidden = false;
  goBtn.disabled = false;
});

// --- Analyze ---
goBtn.addEventListener("click", async () => {
  if (!selectedFile) return;
  goBtn.disabled = true;
  resultEl.hidden = true;
  showStatus("Uploading & running OCR + analysis… (first run loads models, give it a moment)");

  const fd = new FormData();
  fd.append("image", selectedFile);
  fd.append("ocr_backend", $("ocr").value);
  fd.append("analysis_backend", $("analysis").value);
  fd.append("vertical", $("vertical").checked ? "true" : "false");

  try {
    const r = await fetch("/analyze", { method: "POST", body: fd });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: r.statusText }));
      throw new Error(err.detail || `HTTP ${r.status}`);
    }
    const data = await r.json();
    render(data);
    statusEl.hidden = true;
  } catch (e) {
    showStatus("Error: " + e.message, true);
  } finally {
    goBtn.disabled = false;
  }
});

function showStatus(msg, isError = false) {
  statusEl.textContent = msg;
  statusEl.hidden = false;
  statusEl.classList.toggle("error", isError);
}

function render(data) {
  const a = data.analysis;
  $("original").textContent = a.original || data.ocr.text;
  $("ocrBackendLabel").textContent = "· " + data.ocr.backend +
    (data.ocr.confidence != null ? ` (${Math.round(data.ocr.confidence * 100)}%)` : "");
  $("translation").textContent = a.translation || "(no translation)";
  $("analysisBackendLabel").textContent = "· " + data.analysis_backend;

  toggleBlock("readingBlock", "reading", a.reading);

  // tokens
  const tokensBlock = $("tokensBlock");
  const tokens = $("tokens");
  tokens.innerHTML = "";
  if (a.tokens && a.tokens.length) {
    for (const t of a.tokens) tokens.appendChild(tokenEl(t));
    tokensBlock.hidden = false;
  } else {
    tokensBlock.hidden = true;
  }

  // grammar
  const grammarBlock = $("grammarBlock");
  const grammar = $("grammar");
  grammar.innerHTML = "";
  if (a.grammar && a.grammar.length) {
    for (const g of a.grammar) {
      const li = document.createElement("li");
      const pt = document.createElement("span");
      pt.className = "point";
      pt.textContent = g.point + ": ";
      li.appendChild(pt);
      li.appendChild(document.createTextNode(g.explanation));
      grammar.appendChild(li);
    }
    grammarBlock.hidden = false;
  } else {
    grammarBlock.hidden = true;
  }

  toggleBlock("notesBlock", "notes", a.notes);

  const t = data.elapsed_ms || {};
  $("timing").textContent =
    `OCR ${t.ocr_ms ?? "?"}ms · analysis ${t.analysis_ms ?? "?"}ms`;

  resultEl.hidden = false;
}

function toggleBlock(blockId, fieldId, value) {
  const block = $(blockId);
  if (value && value.trim()) {
    $(fieldId).textContent = value;
    block.hidden = false;
  } else {
    block.hidden = true;
  }
}

function tokenEl(t) {
  const el = document.createElement("div");
  el.className = "token";

  const surface = document.createElement("div");
  surface.className = "surface";
  surface.lang = "ja";
  if (t.reading && t.reading !== t.surface) {
    const ruby = document.createElement("ruby");
    ruby.textContent = t.surface;
    const rt = document.createElement("rt");
    rt.textContent = t.reading;
    ruby.appendChild(rt);
    surface.appendChild(ruby);
  } else {
    surface.textContent = t.surface;
  }
  el.appendChild(surface);

  if (t.pos) el.appendChild(div("pos", t.pos));
  if (t.gloss) el.appendChild(div("gloss", t.gloss));
  if (t.note) el.appendChild(div("note", t.note));
  return el;
}

function div(cls, text) {
  const d = document.createElement("div");
  d.className = cls;
  d.textContent = text;
  return d;
}

loadBackends();
