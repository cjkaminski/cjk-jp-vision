"""Mock analysis: always available. Returns a hand-written breakdown of the
sample sentence so the end-to-end pipeline and UI work with zero models."""
from __future__ import annotations

from ..schema import Analysis, GrammarPoint, Token
from .base import AnalysisBackend


class MockAnalysis(AnalysisBackend):
    name = "mock"

    def available(self) -> bool:
        return True

    def install_hint(self) -> str:
        return "Always available (canned demo breakdown)."

    def analyze(self, text: str, token_hint=None) -> Analysis:
        return Analysis(
            original=text,
            translation="I am a cat. As yet I have no name.",
            reading="わがはいはねこである。なまえはまだない。",
            tokens=[
                Token(surface="吾輩", reading="わがはい", romaji="wagahai",
                      pos="pronoun", lemma="吾輩", gloss="I (archaic, lofty)",
                      note="Old first-person pronoun; sets a comic, pompous tone."),
                Token(surface="は", reading="は", romaji="wa", pos="particle",
                      lemma="は", gloss="topic marker"),
                Token(surface="猫", reading="ねこ", romaji="neko", pos="noun",
                      lemma="猫", gloss="cat"),
                Token(surface="である", reading="である", romaji="de aru",
                      pos="copula", lemma="である", gloss="to be",
                      note="Formal/literary copula."),
            ],
            grammar=[
                GrammarPoint(point="〜は〜である",
                             explanation="Topic-comment 'X is Y' using the "
                             "literary copula である instead of です/だ."),
            ],
            notes="This is the mock backend — install a real analysis engine "
            "(claude_cli or local_llm) to analyze your own photos.",
        )
