"""Analysis via the Claude Agent SDK (`claude_agent_sdk`). This runs the Claude
Code engine locally and authenticates with your Claude *plan* (Pro/Max) — no
API key. It's the direct-SDK successor to the `claude_cli` backend: instead of
shelling out to `claude -p` and scraping stdout, we drive the SDK's async
`query()` and read structured messages.

Billing: same plan / Agent SDK credit pool as `claude_cli` (see README).

Auth (important): sign in once with the Claude Code CLI (`claude`). Do NOT set
ANTHROPIC_API_KEY if you want plan billing — a present API key makes the SDK
fall back to pay-as-you-go API billing instead of your plan."""
from __future__ import annotations

import asyncio
import threading
from typing import Coroutine

from ..config import config
from ..schema import Analysis, Token
from .base import AnalysisBackend
from .prompt import SYSTEM, build_prompt, parse_analysis


class ClaudeAgentAnalysis(AnalysisBackend):
    name = "claude_agent"

    def __init__(self) -> None:
        self._checked = False
        self._ok = False

    def available(self) -> bool:
        if not self._checked:
            self._checked = True
            try:
                import claude_agent_sdk  # noqa: F401

                self._ok = True
            except Exception:
                self._ok = False
        return self._ok

    def install_hint(self) -> str:
        return (
            "Install the Agent SDK + Claude Code CLI and sign in with your plan: "
            "`pip install claude-agent-sdk` and "
            "`npm install -g @anthropic-ai/claude-code`, then run `claude` once "
            "to log in. Leave ANTHROPIC_API_KEY unset to bill to your plan."
        )

    def analyze(self, text: str, token_hint: list[Token] | None = None) -> Analysis:
        prompt = build_prompt(text, token_hint)
        raw = _run_sync(self._collect(prompt))
        return parse_analysis(raw, fallback_original=text)

    async def _collect(self, prompt: str) -> str:
        from claude_agent_sdk import (  # imported lazily so import errors are caught
            AssistantMessage,
            ClaudeAgentOptions,
            query,
        )

        kwargs = dict(
            system_prompt=SYSTEM,
            allowed_tools=[],  # pure LLM completion — no file/bash/etc. tools
            max_turns=1,
        )
        if config.CLAUDE_CLI_MODEL:
            kwargs["model"] = config.CLAUDE_CLI_MODEL
        options = ClaudeAgentOptions(**kwargs)

        parts: list[str] = []
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, AssistantMessage):
                for block in getattr(message, "content", None) or []:
                    chunk = getattr(block, "text", None)
                    if chunk:
                        parts.append(chunk)
        return "".join(parts)


def _run_sync(coro: Coroutine):
    """Run an async coroutine from sync code. If we're already inside a running
    event loop (e.g. called directly on the asyncio thread), run it on a fresh
    thread to avoid 'event loop is already running'. In a threadpool worker (the
    normal path from FastAPI), there's no running loop and asyncio.run is used."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    box: dict = {}

    def runner():
        try:
            box["result"] = asyncio.run(coro)
        except BaseException as exc:  # noqa: BLE001 — propagate to caller
            box["error"] = exc

    t = threading.Thread(target=runner)
    t.start()
    t.join()
    if "error" in box:
        raise box["error"]
    return box["result"]
