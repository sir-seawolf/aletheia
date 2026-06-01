"""
REFLECTIVE mode — contradiction detection, pattern analysis, metacognition, drift detection.
"""

from __future__ import annotations

from typing import Any, Dict, List

from core.cognitive_state import CognitiveState
from core.modes.base import CognitiveMode, ModeID, ModeResult

_SYSTEM = (
    "Eres el modo REFLEXIVO de Aletheia. Tu función es detectar contradicciones, "
    "identificar patrones en el comportamiento y el razonamiento, ejercer metacognición "
    "y detectar derivas cognitivas o de valores. Sé honesto incluso cuando incomoda."
)


class ReflectiveMode(CognitiveMode):
    mode_id      = ModeID.REFLECTIVE
    fatigue_cost = 0.05
    min_energy   = 0.1

    def _execute(self, context: Dict[str, Any], state: CognitiveState) -> ModeResult:
        question = context.get("question", "")
        memory   = context.get("memory", [])
        domain   = context.get("domain", "general")

        contradictions = self._detect_contradictions(memory)
        patterns       = self._detect_patterns(memory)

        prompt = (
            f"{_SYSTEM}\n\n"
            f"Dominio: {domain}\n"
            f"Pregunta/reflexión: {question}\n"
            f"Contradicciones detectadas: {contradictions}\n"
            f"Patrones identificados: {patterns}\n\n"
            "Genera una reflexión metacognitiva honesta y acciones correctoras si aplica."
        )

        response = self._llm(
            task="reflective",
            prompt=prompt,
            context={"domain": domain, "mode": "reflective"},
            temp=0.3,
        )

        return ModeResult(
            mode_id         = ModeID.REFLECTIVE,
            output          = {
                "reflection":      response,
                "contradictions":  contradictions,
                "patterns":        patterns,
            },
            confidence      = 0.7,
            tokens_used     = len(prompt.split()) + len(response.split()),
            reasoning_depth = state.preferred_depth,
        )

    def _detect_contradictions(self, memory: List) -> List[str]:
        found = []
        texts = [str(m)[:200].lower() for m in memory[-10:]]
        for i, a in enumerate(texts):
            for b in texts[i + 1:]:
                if _contradicts(a, b):
                    found.append(f"Posible conflicto entre: '{a[:60]}' y '{b[:60]}'")
        return found[:3]

    def _detect_patterns(self, memory: List) -> List[str]:
        from collections import Counter
        words = []
        for m in memory[-20:]:
            words.extend(str(m).lower().split())
        top = Counter(w for w in words if len(w) > 5).most_common(5)
        return [f"{w} ({c}x)" for w, c in top]


def _contradicts(a: str, b: str) -> bool:
    neg_pairs = [("sí", "no"), ("puedo", "no puedo"), ("tengo", "no tengo"),
                 ("quiero", "no quiero"), ("debo", "no debo")]
    for pos, neg in neg_pairs:
        if pos in a and neg in b:
            return True
        if neg in a and pos in b:
            return True
    return False
