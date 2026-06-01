"""OCR backends. Each one is optional and self-reports availability so the
server boots even where a given engine (Apple Vision, manga-ocr) isn't
installed. `get_ocr_backend` resolves a name (or "auto") to an instance."""
from __future__ import annotations

from .base import OCRBackend
from .apple_vision import AppleVisionOCR
from .manga_ocr_backend import MangaOCR
from .mock import MockOCR

# Preference order when OCR_BACKEND=auto. Apple Vision first (best on Mac),
# then manga-ocr (any platform), then the mock so something always answers.
_REGISTRY: list[type[OCRBackend]] = [AppleVisionOCR, MangaOCR, MockOCR]

_instances: dict[str, OCRBackend] = {}


def _instance(cls: type[OCRBackend]) -> OCRBackend:
    if cls.name not in _instances:
        _instances[cls.name] = cls()
    return _instances[cls.name]


def availability() -> dict[str, bool]:
    return {cls.name: _instance(cls).available() for cls in _REGISTRY}


def get_ocr_backend(name: str = "auto") -> OCRBackend:
    if name and name != "auto":
        for cls in _REGISTRY:
            if cls.name == name:
                inst = _instance(cls)
                if not inst.available():
                    raise RuntimeError(
                        f"OCR backend '{name}' is selected but not available. "
                        f"{inst.install_hint()}"
                    )
                return inst
        raise RuntimeError(f"Unknown OCR backend: {name}")

    for cls in _REGISTRY:
        inst = _instance(cls)
        if inst.available():
            return inst
    raise RuntimeError("No OCR backend available.")  # pragma: no cover
