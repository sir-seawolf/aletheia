"""
ANALYTICAL mode — structured logic, debugging, decomposition, validation.
"""

from __future__ import annotations

from typing import Any, Dict

from core.cognitive_state import CognitiveState
from core.modes.base import CognitiveMode, ModeID, ModeResult

_SYSTEM = (
    "Eres el modo ANALÍTICO de Aletheia. Tu función es razonar con lógica estructurada, "
    "descomponer problemas complejos, detectar inconsistencias y validar hipótesis. "
    "Sé preciso, exhaustivo y sistemático. Evita especulaciones sin base."
)


class AnalyticalMode(CognitiveMode):
    mode_id      = ModeID.ANALYTICAL
    fatigue_cost = 0.07
    min_energy   = 0.15

    def _execute(self, context: Dict[str, Any], state: CognitiveState) -> ModeResult:
        question = context.get("question", "")
        domain   = context.get("domain", "general")
        depth    = state.preferred_depth

        steps = self._decompose(question) if depth != "minimal" else [question]

        prompt = (
            f"{_SYSTEM}\n\n"
            f"Dominio: {domain}\n"
            f"Pregunta: {question}\n"
            f"Pasos identificados: {steps}\n\n"
            f"Profundidad de razonamiento: {depth}. "
            "Responde con análisis estructurado."
        )

        response = self._llm(
            task="analytical",
            prompt=prompt,
            context={"domain": domain, "mode": "analytical"},
            temp=0.2,
        )

        return ModeResult(
            mode_id         = ModeID.ANALYTICAL,
            output          = {"analysis": response, "steps": steps},
            confidence      = 0.75,
            tokens_used     = len(prompt.split()) + len(response.split()),
            reasoning_depth = depth,
        )

    def _decompose(self, question: str) -> list[str]:
        parts = [s.strip() for s in question.replace("?", ".").split(".") if len(s.strip()) > 10]
        return parts[:5] if parts else [question]
