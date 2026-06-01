"""The shared instruction + JSON contract used by every LLM-backed analysis
engine, so local and Claude outputs are directly comparable."""
from __future__ import annotations

import json
import re

from ..schema import Analysis, GrammarPoint, Token

SYSTEM = (
    "You are a patient Japanese reading tutor helping an English-speaking "
    "learner understand a passage from a Japanese book. Be accurate and "
    "concise. Always respond with a single JSON object and nothing else."
)

# The JSON shape we ask the model to fill in. Mirrors schema.Analysis.
_SCHEMA_HINT = {
    "original": "the Japanese text, lightly corrected for obvious OCR errors",
    "translation": "natural English translation",
    "reading": "full reading of the passage in hiragana",
    "tokens": [
        {
            "surface": "word as written",
            "reading": "hiragana reading",
            "romaji": "romaji",
            "pos": "part of speech",
            "lemma": "dictionary form",
            "gloss": "short English meaning",
            "note": "conjugation/nuance if relevant",
        }
    ],
    "grammar": [
        {"point": "grammar pattern", "explanation": "how it's used here"}
    ],
    "notes": "overall notes, ambiguity, or cultural context",
}


def build_prompt(text: str, token_hint: list[Token] | None = None) -> str:
    parts = [
        "Analyze this Japanese passage for a learner.",
        "",
        "PASSAGE:",
        text,
        "",
    ]
    if token_hint:
        scaffold = "  ".join(
            f"{t.surface}({t.reading}/{t.pos})" for t in token_hint if t.surface
        )
        parts += [
            "A morphological tokenizer suggested this segmentation (use it as a "
            "hint, correct it if wrong):",
            scaffold,
            "",
        ]
    parts += [
        "Respond with ONE JSON object using exactly this shape "
        "(fill every field; arrays may be empty if truly nothing applies):",
        json.dumps(_SCHEMA_HINT, ensure_ascii=False, indent=2),
    ]
    return "\n".join(parts)


def parse_analysis(raw: str, fallback_original: str) -> Analysis:
    """Extract the JSON object from a model reply (tolerating ```json fences
    and surrounding prose) and coerce it into an Analysis."""
    obj = _extract_json(raw)
    if obj is None:
        # Model didn't give JSON; treat the whole reply as a translation.
        return Analysis(original=fallback_original, translation=raw.strip())

    tokens = [Token(**t) for t in obj.get("tokens", []) if isinstance(t, dict)]
    grammar = [
        GrammarPoint(**g) for g in obj.get("grammar", []) if isinstance(g, dict)
    ]
    return Analysis(
        original=obj.get("original") or fallback_original,
        translation=obj.get("translation", ""),
        reading=obj.get("reading", ""),
        tokens=tokens,
        grammar=grammar,
        notes=obj.get("notes", ""),
    )


def _extract_json(raw: str):
    if not raw:
        return None
    raw = raw.strip()
    # strip ```json ... ``` fences if present
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", raw, re.DOTALL)
    if fence:
        raw = fence.group(1)
    # find the first balanced {...}
    start = raw.find("{")
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(raw)):
        if raw[i] == "{":
            depth += 1
        elif raw[i] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(raw[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None
