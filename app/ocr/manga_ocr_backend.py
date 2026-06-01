"""manga-ocr backend. Works on any platform (Mac/Linux/Windows). Purpose-built
for printed Japanese (manga/novels) and handles vertical text well. Loads a
torch model on first use, so construction stays lazy."""
from __future__ import annotations

import io

from ..schema import OCRResult
from .base import OCRBackend


class MangaOCR(OCRBackend):
    name = "manga_ocr"

    def __init__(self) -> None:
        self._checked = False
        self._importable = False
        self._model = None

    def available(self) -> bool:
        if not self._checked:
            self._checked = True
            try:
                import manga_ocr  # noqa: F401

                self._importable = True
            except Exception:
                self._importable = False
        return self._importable

    def install_hint(self) -> str:
        return "Install with `pip install manga-ocr` (pulls in torch)."

    def _ensure_model(self):
        if self._model is None:
            from manga_ocr import MangaOcr

            self._model = MangaOcr()
        return self._model

    def recognize(self, image_bytes: bytes, vertical: bool = True) -> OCRResult:
        from PIL import Image

        model = self._ensure_model()
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        # manga-ocr expects a single text region per call. For a full page this
        # returns one block; for best results the UI can crop to a passage.
        text = model(img)
        return OCRResult(text=text, backend=self.name, confidence=None)
