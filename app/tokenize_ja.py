"""Optional MeCab/fugashi tokenizer. Provides deterministic, dictionary-grade
word segmentation + readings that we can hand to the LLM as a scaffold (and
show even if the LLM is unavailable). Degrades silently if fugashi isn't
installed."""
from __future__ import annotations

from .schema import Token

_KATA = "ァアィイゥウェエォオカガキギクグケゲコゴサザシジスゼセゼソゾタダチヂッツヅテデトドナニヌネノハバパヒビピフブプヘベペホボポマミムメモャヤュユョヨラリルレロヮワヰヱヲンヴ"


def _kata_to_hira(s: str) -> str:
    out = []
    for ch in s:
        code = ord(ch)
        if 0x30A1 <= code <= 0x30F6:  # katakana block -> hiragana
            out.append(chr(code - 0x60))
        else:
            out.append(ch)
    return "".join(out)


class Tokenizer:
    def __init__(self) -> None:
        self._tagger = None
        self._ok = False
        try:
            import fugashi

            self._tagger = fugashi.Tagger()
            self._ok = True
        except Exception:
            self._ok = False

    @property
    def available(self) -> bool:
        return self._ok

    def tokenize(self, text: str) -> list[Token]:
        if not self._ok or not text:
            return []
        tokens: list[Token] = []
        for word in self._tagger(text):
            surface = word.surface
            if not surface.strip():
                continue
            feat = word.feature
            pos = getattr(feat, "pos1", "") or ""
            lemma = getattr(feat, "lemma", "") or surface
            kana = getattr(feat, "kana", None) or getattr(feat, "pron", None) or ""
            reading = _kata_to_hira(kana) if kana else ""
            tokens.append(
                Token(surface=surface, reading=reading, pos=pos, lemma=lemma)
            )
        return tokens
