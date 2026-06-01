"""Apple Vision OCR (macOS only) via pyobjc. Vision's Japanese recognition is
excellent for printed text. We do a best-effort geometric reorder for vertical
(tategaki) novels, since Vision returns observations without reading order."""
from __future__ import annotations

from ..schema import OCRResult
from .base import OCRBackend


class AppleVisionOCR(OCRBackend):
    name = "apple_vision"

    def __init__(self) -> None:
        self._checked = False
        self._ok = False

    def available(self) -> bool:
        if not self._checked:
            self._checked = True
            try:
                import Quartz  # noqa: F401
                import Vision  # noqa: F401

                self._ok = True
            except Exception:
                self._ok = False
        return self._ok

    def install_hint(self) -> str:
        return (
            "Apple Vision needs macOS + pyobjc: "
            "`pip install pyobjc-framework-Vision pyobjc-framework-Quartz`"
        )

    def recognize(self, image_bytes: bytes, vertical: bool = True) -> OCRResult:
        import Quartz
        import Vision
        from Foundation import NSData

        data = NSData.dataWithBytes_length_(image_bytes, len(image_bytes))
        src = Quartz.CGImageSourceCreateWithData(data, None)
        if src is None:
            raise RuntimeError("Apple Vision: could not decode image.")
        cg_image = Quartz.CGImageSourceCreateImageAtIndex(src, 0, None)

        handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_options_(
            cg_image, None
        )
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLanguages_(["ja", "en"])
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)
        request.setUsesLanguageCorrection_(True)

        ok = handler.performRequests_error_([request], None)
        if not ok:
            raise RuntimeError("Apple Vision: recognition request failed.")

        observations = request.results() or []
        items = []
        confidences = []
        for obs in observations:
            cand = obs.topCandidates_(1)
            if not cand:
                continue
            top = cand[0]
            box = obs.boundingBox()  # normalized, origin bottom-left
            # CGRect -> origin.x, origin.y, size.width, size.height
            x = box.origin.x
            y = box.origin.y
            items.append((x, y, top.string()))
            confidences.append(float(top.confidence()))

        ordered = _reorder(items, vertical=vertical)
        text = "\n".join(s for _, _, s in ordered)
        conf = sum(confidences) / len(confidences) if confidences else None
        return OCRResult(text=text, backend=self.name, confidence=conf)


def _reorder(items, vertical: bool):
    """Best-effort reading order. Horizontal: top-to-bottom, left-to-right.
    Vertical (tategaki): right column first, top-to-bottom within a column.
    Coordinates are normalized with origin at the BOTTOM-left."""
    if not items:
        return items
    if not vertical:
        # rows by descending y (top first), then ascending x (left first)
        return sorted(items, key=lambda it: (-round(it[1], 2), it[0]))

    # Vertical: cluster into columns by x, columns ordered right (high x) to left.
    xs = sorted({round(x, 2) for x, _, _ in items})
    # group nearby x values into columns
    columns: list[list] = []
    threshold = 0.04
    for it in sorted(items, key=lambda i: -i[0]):  # right to left
        placed = False
        for col in columns:
            if abs(col[0][0] - it[0]) <= threshold:
                col.append(it)
                placed = True
                break
        if not placed:
            columns.append([it])
    out = []
    for col in columns:
        # within a column, top (high y) to bottom (low y)
        out.extend(sorted(col, key=lambda i: -i[1]))
    return out
