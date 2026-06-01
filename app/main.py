"""FastAPI server: serves the camera web page and an /analyze endpoint that
runs OCR then LLM analysis. Backends are chosen per-request (or "auto")."""
from __future__ import annotations

import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import analysis as analysis_mod
from . import ocr as ocr_mod
from .config import config
from .schema import AnalyzeResponse, HealthResponse
from .tokenize_ja import Tokenizer

app = FastAPI(title="cjk-jp-vision", version="0.1.0")

WEB_DIR = Path(__file__).resolve().parent.parent / "web"

# One shared tokenizer (loads MeCab dict once).
_tokenizer = Tokenizer() if config.USE_MECAB else None


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        ok=True,
        ocr_backends=ocr_mod.availability(),
        analysis_backends=analysis_mod.availability(),
        mecab=bool(_tokenizer and _tokenizer.available),
    )


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    image: UploadFile = File(...),
    ocr_backend: str = Form("auto"),
    analysis_backend: str = Form("auto"),
    vertical: bool = Form(True),
) -> AnalyzeResponse:
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image upload.")

    timings: dict[str, int] = {}

    # --- OCR ---
    t0 = time.perf_counter()
    try:
        ocr = ocr_mod.get_ocr_backend(ocr_backend)
        ocr_result = ocr.recognize(image_bytes, vertical=vertical)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR failed: {e}")
    timings["ocr_ms"] = int((time.perf_counter() - t0) * 1000)

    if not ocr_result.text.strip():
        raise HTTPException(status_code=422, detail="OCR produced no text.")

    # --- Tokenize (optional scaffold for the LLM) ---
    token_hint = (
        _tokenizer.tokenize(ocr_result.text)
        if _tokenizer and _tokenizer.available
        else []
    )

    # --- Analysis ---
    t1 = time.perf_counter()
    try:
        engine = analysis_mod.get_analysis_backend(analysis_backend)
        result = engine.analyze(ocr_result.text, token_hint=token_hint)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
    timings["analysis_ms"] = int((time.perf_counter() - t1) * 1000)

    # If the analysis engine didn't fill tokens but MeCab did, use those.
    if not result.tokens and token_hint:
        result.tokens = token_hint

    return AnalyzeResponse(
        ocr=ocr_result,
        analysis=result,
        analysis_backend=engine.name,
        elapsed_ms=timings,
    )


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


# Serve static assets (app.js, style.css) under /static
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


def main() -> None:
    import uvicorn

    uvicorn.run(app, host=config.HOST, port=config.PORT)


if __name__ == "__main__":
    main()
