"""Mock OCR: always available, returns a fixed sample passage. Lets you smoke-
test the whole pipeline (and the UI) without any model installed."""
from __future__ import annotations

from ..schema import OCRResult
from .base import OCRBackend

SAMPLE = "吾輩は猫である。名前はまだ無い。"


class MockOCR(OCRBackend):
    name = "mock"

    def available(self) -> bool:
        return True

    def install_hint(self) -> str:
        return "Always available (returns a canned sample)."

    def recognize(self, image_bytes: bytes, vertical: bool = True) -> OCRResult:
        return OCRResult(text=SAMPLE, backend=self.name, confidence=1.0)
