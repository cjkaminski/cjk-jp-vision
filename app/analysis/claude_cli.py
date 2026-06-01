"""Analysis via the Claude Code CLI. Authenticates with your Claude plan, so
no API key is needed. We shell out to `claude -p` and parse the JSON it returns.

Billing (as of June 2026): before 2026-06-15 this draws from your normal
subscription usage limits; from 2026-06-15 it draws from a separate monthly
Agent SDK credit (Max 20x: ~$200/mo) that explicitly covers `claude -p` and
apps built on the Agent SDK. See README for details. The Anthropic *API*
(anthropic_api backend) bills separately as pay-as-you-go."""
from __future__ import annotations

import shutil
import subprocess

from ..config import config
from ..schema import Analysis, Token
from .base import AnalysisBackend
from .prompt import SYSTEM, build_prompt, parse_analysis


class ClaudeCLIAnalysis(AnalysisBackend):
    name = "claude_cli"

    def available(self) -> bool:
        return shutil.which(config.CLAUDE_CLI_PATH) is not None

    def install_hint(self) -> str:
        return (
            "Install the Claude Code CLI and sign in with your Max subscription: "
            "`npm install -g @anthropic-ai/claude-code` then `claude` once to log in."
        )

    def analyze(self, text: str, token_hint: list[Token] | None = None) -> Analysis:
        prompt = build_prompt(text, token_hint)
        cmd = [
            config.CLAUDE_CLI_PATH,
            "-p",
            prompt,
            "--append-system-prompt",
            SYSTEM,
            "--output-format",
            "text",
        ]
        if config.CLAUDE_CLI_MODEL:
            cmd += ["--model", config.CLAUDE_CLI_MODEL]

        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if proc.returncode != 0:
            raise RuntimeError(
                f"claude CLI failed ({proc.returncode}): {proc.stderr.strip()[:500]}"
            )
        return parse_analysis(proc.stdout, fallback_original=text)
