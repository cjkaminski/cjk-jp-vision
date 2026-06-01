"""Tiny end-to-end smoke test using the mock backends. Runs with zero models
installed and no network — proves the wiring (OCR -> analysis -> response).

    python scripts/smoke_test.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import analysis as analysis_mod  # noqa: E402
from app import ocr as ocr_mod  # noqa: E402


def main() -> int:
    ocr = ocr_mod.get_ocr_backend("mock")
    ocr_result = ocr.recognize(b"not-a-real-image", vertical=True)
    assert ocr_result.text, "mock OCR returned empty text"

    engine = analysis_mod.get_analysis_backend("mock")
    analysis = engine.analyze(ocr_result.text)
    assert analysis.translation, "mock analysis returned empty translation"
    assert analysis.tokens, "mock analysis returned no tokens"

    print("OCR  :", ocr_result.text)
    print("EN   :", analysis.translation)
    print("Tokens:", len(analysis.tokens))
    print("OCR backends     :", ocr_mod.availability())
    print("Analysis backends:", analysis_mod.availability())
    print("\nSmoke test PASSED ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
