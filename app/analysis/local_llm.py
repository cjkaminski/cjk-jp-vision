"""Analysis via a local, OpenAI-compatible LLM endpoint — point this at Ollama
or vLLM running on your Blackwell GPU box. This is the "fully local" engine for
your quality comparison against Claude."""
from __future__ import annotations

import httpx

from ..config import config
from ..schema import Analysis, Token
from .base import AnalysisBackend
from .prompt import SYSTEM, build_prompt, parse_analysis


class LocalLLMAnalysis(AnalysisBackend):
    name = "local_llm"

    def available(self) -> bool:
        # Cheap reachability check against the OpenAI-compatible models endpoint.
        url = config.LOCAL_LLM_BASE_URL.rstrip("/") + "/models"
        try:
            r = httpx.get(
                url,
                headers={"Authorization": f"Bearer {config.LOCAL_LLM_API_KEY}"},
                timeout=2.0,
            )
            return r.status_code < 500
        except Exception:
            return False

    def install_hint(self) -> str:
        return (
            f"Start an OpenAI-compatible server at {config.LOCAL_LLM_BASE_URL} "
            "(e.g. Ollama: `ollama serve` + `ollama pull "
            f"{config.LOCAL_LLM_MODEL}`, or vLLM on the GPU box)."
        )

    def analyze(self, text: str, token_hint: list[Token] | None = None) -> Analysis:
        prompt = build_prompt(text, token_hint)
        url = config.LOCAL_LLM_BASE_URL.rstrip("/") + "/chat/completions"
        payload = {
            "model": config.LOCAL_LLM_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            # Many local servers honor this for cleaner JSON; ignored if unsupported.
            "response_format": {"type": "json_object"},
        }
        with httpx.Client(timeout=120) as client:
            r = client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {config.LOCAL_LLM_API_KEY}"},
            )
            r.raise_for_status()
            data = r.json()
        content = data["choices"][0]["message"]["content"]
        return parse_analysis(content, fallback_original=text)
