"""Analysis via the Anthropic API (needs a real API key + API billing — this is
NOT covered by a Max subscription). Optional; handy if you ever want it. Uses
httpx directly to avoid requiring the anthropic SDK."""
from __future__ import annotations

import httpx

from ..config import config
from ..schema import Analysis, Token
from .base import AnalysisBackend
from .prompt import SYSTEM, build_prompt, parse_analysis


class AnthropicAPIAnalysis(AnalysisBackend):
    name = "anthropic_api"

    def available(self) -> bool:
        return bool(config.ANTHROPIC_API_KEY)

    def install_hint(self) -> str:
        return (
            "Set ANTHROPIC_API_KEY in .env. Note: API usage is billed separately "
            "from your Max subscription."
        )

    def analyze(self, text: str, token_hint: list[Token] | None = None) -> Analysis:
        prompt = build_prompt(text, token_hint)
        with httpx.Client(timeout=120) as client:
            r = client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": config.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": config.ANTHROPIC_MODEL,
                    "max_tokens": 2048,
                    "system": SYSTEM,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            r.raise_for_status()
            data = r.json()
        content = "".join(
            block.get("text", "") for block in data.get("content", [])
        )
        return parse_analysis(content, fallback_original=text)
