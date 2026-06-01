"""Configuration pulled from environment / .env. Kept dependency-free
(no pydantic-settings) so it's obvious what's read and from where."""
from __future__ import annotations

import os
from pathlib import Path


def _load_dotenv() -> None:
    """Minimal .env loader so we don't add a dependency just for this.
    Does not override variables already set in the real environment."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for raw in env_path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


class Config:
    # OCR
    OCR_BACKEND = _get("OCR_BACKEND", "auto")

    # Analysis
    ANALYSIS_BACKEND = _get("ANALYSIS_BACKEND", "auto")
    CLAUDE_CLI_PATH = _get("CLAUDE_CLI_PATH", "claude")
    CLAUDE_CLI_MODEL = _get("CLAUDE_CLI_MODEL", "")

    LOCAL_LLM_BASE_URL = _get("LOCAL_LLM_BASE_URL", "http://localhost:11434/v1")
    LOCAL_LLM_MODEL = _get("LOCAL_LLM_MODEL", "qwen2.5:14b-instruct")
    LOCAL_LLM_API_KEY = _get("LOCAL_LLM_API_KEY", "not-needed")

    ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY", "")
    ANTHROPIC_MODEL = _get("ANTHROPIC_MODEL", "claude-opus-4-8")

    # Tokenizer
    USE_MECAB = _get("USE_MECAB", "1") == "1"

    # Server
    HOST = _get("HOST", "0.0.0.0")
    PORT = int(_get("PORT", "8000"))


config = Config()
