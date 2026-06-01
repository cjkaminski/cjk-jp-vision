# cjk-jp-vision

Photograph a passage from a Japanese book on your phone, OCR it, and get a
**learner-focused breakdown**: natural translation, full reading (furigana),
word-by-word gloss, and grammar notes. Built for studying Japanese by reading
real books.

It's a small self-hosted web app: a mobile-friendly page that uses your
**iPhone camera**, talking to a server **you run on your own machine** that does
the OCR and the language analysis. No third-party services are required (though
you can optionally use Claude or a hosted API for the analysis step).

## How it answers the original questions

- **Can a web app use the iPhone camera?** Yes. The page uses
  `<input type="file" accept="image/*" capture="environment">`, which opens the
  native iOS camera. This works over plain HTTP (no `getUserMedia`), so you
  don't need an HTTPS certificate just to capture a photo.
- **Can it send photos to a server on my own workstation?** Yes. The phone POSTs
  the image to your server; the server runs the models and returns JSON.

## Architecture

```
 iPhone (Safari)                 Your machine(s)
 ┌───────────────┐   photo      ┌──────────────────────────────────────┐
 │ camera page   │ ───────────▶ │ FastAPI server                       │
 │ (web/)        │              │  1. OCR backend  ─ Apple Vision (Mac) │
 │               │ ◀─────────── │                  ─ manga-ocr (any OS) │
 └───────────────┘   JSON       │  2. MeCab tokenize (optional)         │
                                │  3. Analysis backend                  │
                                │     ─ claude_cli  (Max subscription)  │
                                │     ─ local_llm   (your GPU box)      │
                                │     ─ anthropic_api (optional)        │
                                └──────────────────────────────────────┘
```

Every OCR and analysis engine is **pluggable and self-reporting** — the server
boots even if a given engine isn't installed, and the web UI lets you switch
engines per request so you can **compare quality** (e.g. local model vs. Claude).

### Your hardware maps cleanly onto this

- **MacBook Pro (M3):** run the server here. It gets **Apple Vision** OCR
  (excellent Japanese, via pyobjc) and can drive the **`claude` CLI** under your
  Max subscription — no API key needed.
- **Linux + Blackwell GPUs:** run a local LLM (Ollama or vLLM) exposing an
  OpenAI-compatible endpoint; point `LOCAL_LLM_BASE_URL` at it for the
  fully-local analysis engine.

## A note on "using my Max subscription" (important)

Your **Max subscription is not the same as Anthropic API credits** — there's no
bundled API spend, and an API key bills separately. But you *can* use your
subscription for the analysis step via the **`claude_cli` backend**, which shells
out to the Claude Code CLI (authenticated with your plan). That's the
no-API-key path. The `anthropic_api` backend is also included if you ever want
to use a real API key (billed separately).

## Quick start

```bash
cp .env.example .env          # edit if you like; defaults are sane
python3 scripts/smoke_test.py # verify wiring with mock backends (no models)
bash scripts/run.sh           # start the server on :8000
```

Open `http://localhost:8000` on the same machine to try it with the **mock**
backends immediately. Then install real engines (below) and reload.

### Install the real engines

```bash
# OCR — pick what your platform supports:
pip install pyobjc-framework-Vision pyobjc-framework-Quartz   # Apple Vision (macOS)
pip install manga-ocr                                          # any OS (pulls torch)

# Tokenizer (recommended): deterministic word segmentation + readings
pip install fugashi unidic-lite

# Analysis via your Max subscription:
npm install -g @anthropic-ai/claude-code   # then run `claude` once to sign in

# Analysis via local GPU model (on the Linux box):
#   ollama serve && ollama pull qwen2.5:14b-instruct
#   then set LOCAL_LLM_BASE_URL / LOCAL_LLM_MODEL in .env
```

`GET /health` reports exactly which backends are live.

## Reaching the server from your iPhone

The camera capture works over HTTP, so the simplest setup needs **no
certificate**:

- **Tailscale (recommended to start):** put phone + workstation on your tailnet,
  then open `http://<workstation-tailnet-ip>:8000`. Private, zero cert hassle.
- **Same Wi-Fi:** open `http://<workstation-lan-ip>:8000`.
- **Cloudflare Tunnel / ngrok:** gives a public `https://` URL — needed only if
  you later add the live-preview camera (`getUserMedia`), which iOS requires
  HTTPS for. The current file-capture UI does not need it.

## Tips for good OCR on book pages

- Vertical novels: keep the **"Vertical text (tategaki)"** toggle on.
- Fill the frame with the passage; flat, even lighting; avoid the page curve.
- For dense pages, photograph **one passage** rather than the whole spread —
  OCR and the breakdown are both sharper on a focused region.

## Layout

```
app/
  main.py          FastAPI server (/, /health, /analyze)
  config.py        env / .env settings
  schema.py        shared pydantic models
  ocr/             apple_vision · manga_ocr · mock  (+ base, factory)
  analysis/        claude_cli · local_llm · anthropic_api · mock (+ prompt, base)
  tokenize_ja.py   optional MeCab/fugashi tokenizer
web/               index.html · app.js · style.css  (the camera page)
scripts/           run.sh · smoke_test.py
```

## Status

Prototype. The pipeline is wired and tested end-to-end with mock backends; the
real OCR/LLM engines are integrated and ready to enable on your hardware. Next
candidates: in-browser crop-to-passage before upload, JMdict gloss enrichment,
and saving a study log of looked-up sentences.
