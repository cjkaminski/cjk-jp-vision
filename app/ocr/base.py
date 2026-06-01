from __future__ import annotations

from abc import ABC, abstractmethod

from ..schema import OCRResult


class OCRBackend(ABC):
    """Turn image bytes into Japanese text. Implementations must be cheap to
    construct (do heavy imports/model loads lazily) so `available()` is fast."""

    name: str = "base"

    @abstractmethod
    def available(self) -> bool:
        """True if this backend can actually run on this machine right now."""

    def install_hint(self) -> str:
        return ""

    @abstractmethod
    def recognize(self, image_bytes: bytes, vertical: bool = True) -> OCRResult:
        """Recognize text. `vertical` hints that the source is vertical writing
        (tategaki), which is the common case for novels."""
