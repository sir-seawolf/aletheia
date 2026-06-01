"""
CREATIVE mode — ideation, synthesis, associative thinking, narrative generation.
"""

from __future__ import annotations

from typing import Any, Dict

from core.cognitive_state import CognitiveState
from core.modes.base import CognitiveMode, ModeID, ModeResult

_SYSTEM = (
    "Eres el modo CREATIVO de Aletheia. Tu función es generar ideas originales, "
    "conectar conceptos aparentemente no relacionados, sintetizar soluciones innovadoras "
    "y construir narrativas poderosas. Prioriza la originalidad sobre la seguridad."
)


class CreativeMode(CognitiveMode):
    mode_id      = ModeID.CREATIVE
    fatigue_cost = 0.06
    min_energy   = 0.2

    def _execute(self, context: Dict[str, Any], state: CognitiveState) -> ModeResult:
        question = context.get("question", "")
        domain   = context.get("domain", "general")

        prompt = (
            f"{_SYSTEM}\n\n"
            f"Dominio: {domain}\n"
            f"Solicitud: {question}\n\n"
            "Genera al menos 3 ideas originales. Para cada una: título, descripción breve, "
            "posible impacto."
        )

        response = self._llm(
            task="creative",
            prompt=prompt,
            context={"domain": domain, "mode": "creative"},
            temp=0.8,
        )

        return ModeResult(
            mode_id         = ModeID.CREATIVE,
            output          = {"ideas": response},
            confidence      = 0.65,
            tokens_used     = len(prompt.split()) + len(response.split()),
            reasoning_depth = state.preferred_depth,
        )
