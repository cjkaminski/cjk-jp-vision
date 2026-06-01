"""Shared response models. The whole app speaks these shapes so the OCR and
analysis backends stay swappable."""
from __future__ import annotations

from pydantic import BaseModel, Field


class Token(BaseModel):
    """One word/morpheme from the sentence breakdown."""

    surface: str = Field(description="The text as it appears in the sentence.")
    reading: str = Field("", description="Reading in hiragana (furigana).")
    romaji: str = Field("", description="Romanized reading.")
    pos: str = Field("", description="Part of speech, e.g. noun, verb, particle.")
    lemma: str = Field("", description="Dictionary (base) form.")
    gloss: str = Field("", description="Short English meaning.")
    note: str = Field("", description="Anything notable: conjugation, nuance, etc.")


class GrammarPoint(BaseModel):
    point: str = Field(description="The grammar pattern, e.g. ～ている, ～なければならない.")
    explanation: str = Field(description="What it does / how it's used here.")


class Analysis(BaseModel):
    """The learner-facing result for one OCR'd passage."""

    original: str = Field(description="The Japanese text as OCR'd (possibly corrected).")
    translation: str = Field("", description="Natural English translation.")
    reading: str = Field("", description="Full reading of the passage in kana.")
    tokens: list[Token] = Field(default_factory=list)
    grammar: list[GrammarPoint] = Field(default_factory=list)
    notes: str = Field("", description="Overall notes, cultural context, ambiguities.")


class OCRResult(BaseModel):
    text: str = Field(description="Recognized Japanese text.")
    backend: str = Field(description="Which OCR engine produced this.")
    confidence: float | None = Field(
        None, description="Best-effort confidence 0..1 if the engine reports it."
    )


class AnalyzeResponse(BaseModel):
    ocr: OCRResult
    analysis: Analysis
    analysis_backend: str = Field(description="Which analysis engine was used.")
    elapsed_ms: dict[str, int] = Field(
        default_factory=dict, description="Timing per stage for the curious."
    )


class HealthResponse(BaseModel):
    ok: bool = True
    ocr_backends: dict[str, bool]
    analysis_backends: dict[str, bool]
    mecab: bool
