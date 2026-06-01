"""Analysis via the Claude Code CLI. This authenticates with your Max
subscription (no API key, no per-call API billing). We shell out to
`claude -p` with the prompt and parse the JSON it returns.

This is the "use my subscription" path you asked about: the Anthropic *API*
needs separate billing, but the CLI runs under your existing Claude plan."""
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
