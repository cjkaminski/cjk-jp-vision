from __future__ import annotations

from abc import ABC, abstractmethod

from ..schema import Analysis, Token


class AnalysisBackend(ABC):
    name: str = "base"

    @abstractmethod
    def available(self) -> bool:
        ...

    def install_hint(self) -> str:
        return ""

    @abstractmethod
    def analyze(self, text: str, token_hint: list[Token] | None = None) -> Analysis:
        ...
