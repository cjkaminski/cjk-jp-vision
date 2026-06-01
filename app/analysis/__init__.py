"""Analysis backends: translation + learner breakdown. Pluggable so you can
compare a local GPU model against Claude-via-subscription on the same passage."""
from __future__ import annotations

from .base import AnalysisBackend
from .claude_cli import ClaudeCLIAnalysis
from .local_llm import LocalLLMAnalysis
from .anthropic_api import AnthropicAPIAnalysis
from .mock import MockAnalysis

# Preference for ANALYSIS_BACKEND=auto: Claude CLI (uses Max subscription) first,
# then local GPU model, then API, then mock.
_REGISTRY: list[type[AnalysisBackend]] = [
    ClaudeCLIAnalysis,
    LocalLLMAnalysis,
    AnthropicAPIAnalysis,
    MockAnalysis,
]

_instances: dict[str, AnalysisBackend] = {}


def _instance(cls: type[AnalysisBackend]) -> AnalysisBackend:
    if cls.name not in _instances:
        _instances[cls.name] = cls()
    return _instances[cls.name]


def availability() -> dict[str, bool]:
    return {cls.name: _instance(cls).available() for cls in _REGISTRY}


def get_analysis_backend(name: str = "auto") -> AnalysisBackend:
    if name and name != "auto":
        for cls in _REGISTRY:
            if cls.name == name:
                inst = _instance(cls)
                if not inst.available():
                    raise RuntimeError(
                        f"Analysis backend '{name}' selected but not available. "
                        f"{inst.install_hint()}"
                    )
                return inst
        raise RuntimeError(f"Unknown analysis backend: {name}")

    for cls in _REGISTRY:
        inst = _instance(cls)
        if inst.available():
            return inst
    raise RuntimeError("No analysis backend available.")  # pragma: no cover
