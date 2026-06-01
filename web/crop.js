"use strict";

/**
 * JPCrop: a small touch-friendly crop tool.
 *
 * The user drags across the photo to select a passage; we keep the selection
 * in *natural image coordinates* (so it survives rotation/resize) and export
 * just that region as a JPEG at full source resolution (capped to MAX_DIM).
 *
 * Doing the crop here also re-encodes HEIC/PNG to JPEG, which keeps the server
 * simple and works the same across Safari/Brave/Firefox on iOS (all WebKit).
 */
window.JPCrop = (function () {
  const MAX_DIM = 2000; // cap the longest exported side; plenty for OCR
  const MIN_SEL = 12; // ignore tiny accidental drags (display px)

  let canvas, ctx, img;
  let scale = 1; // display px per natural px
  let selNat = null; // {x,y,w,h} in NATURAL image coords, or null = whole image
  let drawing = false;
  let startNat = null;

  function init(canvasEl) {
    canvas = canvasEl;
    ctx = canvas.getContext("2d");
    canvas.addEventListener("pointerdown", onDown);
    canvas.addEventListener("pointermove", onMove);
    canvas.addEventListener("pointerup", onUp);
    canvas.addEventListener("pointercancel", onUp);
    window.addEventListener("resize", () => {
      if (img) {
        fit();
        draw();
      }
    });
  }

  function load(file) {
    return new Promise((resolve, reject) => {
      const url = URL.createObjectURL(file);
      const im = new Image();
      im.onload = () => {
        URL.revokeObjectURL(url);
        img = im;
        selNat = null;
        fit();
        draw();
        resolve();
      };
      im.onerror = (e) => {
        URL.revokeObjectURL(url);
        reject(new Error("Could not load image (unsupported format?)"));
      };
      im.src = url;
    });
  }

  function fit() {
    const maxW = canvas.parentElement.clientWidth || window.innerWidth;
    const maxH = Math.max(240, Math.min(window.innerHeight * 0.6, 820));
    scale = Math.min(maxW / img.naturalWidth, maxH / img.naturalHeight, 1);
    canvas.width = Math.round(img.naturalWidth * scale);
    canvas.height = Math.round(img.naturalHeight * scale);
  }

  // Map a pointer event to NATURAL image coordinates, robust to CSS scaling.
  function evtNat(e) {
    const r = canvas.getBoundingClientRect();
    const dx = (e.clientX - r.left) * (canvas.width / r.width);
    const dy = (e.clientY - r.top) * (canvas.height / r.height);
    return {
      x: clamp(dx / scale, 0, img.naturalWidth),
      y: clamp(dy / scale, 0, img.naturalHeight),
    };
  }

  function onDown(e) {
    if (!img) return;
    e.preventDefault();
    canvas.setPointerCapture(e.pointerId);
    drawing = true;
    startNat = evtNat(e);
    selNat = { x: startNat.x, y: startNat.y, w: 0, h: 0 };
    draw();
  }

  function onMove(e) {
    if (!drawing) return;
    e.preventDefault();
    const p = evtNat(e);
    selNat = rectFrom(startNat, p);
    draw();
  }

  function onUp(e) {
    if (!drawing) return;
    drawing = false;
    // Discard a too-small selection (treat as "whole image").
    if (selNat && (selNat.w * scale < MIN_SEL || selNat.h * scale < MIN_SEL)) {
      selNat = null;
    }
    draw();
    if (typeof onChange === "function") onChange(hasSelection());
  }

  function draw() {
    if (!img) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    if (!selNat) return;

    const d = toDisplay(selNat);
    // Dim everything, then "spotlight" the selection back to full brightness.
    ctx.fillStyle = "rgba(0,0,0,0.55)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(
      img,
      selNat.x, selNat.y, selNat.w, selNat.h,
      d.x, d.y, d.w, d.h
    );
    ctx.strokeStyle = "#e0533d";
    ctx.lineWidth = 2;
    ctx.strokeRect(d.x + 1, d.y + 1, d.w - 2, d.h - 2);
  }

  function reset() {
    selNat = null;
    draw();
    if (typeof onChange === "function") onChange(false);
  }

  function hasSelection() {
    return !!selNat;
  }

  // Export the selected region (or the whole image) as a JPEG Blob.
  function getBlob(quality = 0.92) {
    return new Promise((resolve, reject) => {
      if (!img) return reject(new Error("No image loaded."));
      const region = selNat || {
        x: 0,
        y: 0,
        w: img.naturalWidth,
        h: img.naturalHeight,
      };
      // Scale down if the region exceeds MAX_DIM on its longest side.
      const longest = Math.max(region.w, region.h);
      const k = longest > MAX_DIM ? MAX_DIM / longest : 1;
      const outW = Math.max(1, Math.round(region.w * k));
      const outH = Math.max(1, Math.round(region.h * k));

      const out = document.createElement("canvas");
      out.width = outW;
      out.height = outH;
      const octx = out.getContext("2d");
      octx.drawImage(img, region.x, region.y, region.w, region.h, 0, 0, outW, outH);
      out.toBlob(
        (blob) => (blob ? resolve(blob) : reject(new Error("toBlob failed"))),
        "image/jpeg",
        quality
      );
    });
  }

  // --- helpers ---
  let onChange = null;
  function setOnChange(fn) {
    onChange = fn;
  }
  function toDisplay(r) {
    return { x: r.x * scale, y: r.y * scale, w: r.w * scale, h: r.h * scale };
  }
  function rectFrom(a, b) {
    return {
      x: Math.min(a.x, b.x),
      y: Math.min(a.y, b.y),
      w: Math.abs(a.x - b.x),
      h: Math.abs(a.y - b.y),
    };
  }
  function clamp(v, lo, hi) {
    return Math.max(lo, Math.min(hi, v));
  }

  return { init, load, getBlob, reset, hasSelection, setOnChange };
})();
