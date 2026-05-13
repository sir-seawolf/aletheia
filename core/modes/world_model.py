"""
WORLD_MODEL mode — systems thinking, causal analysis, multi-domain simulation.
"""

from __future__ import annotations

from typing import Any, Dict

from core.cognitive_state import CognitiveState
from core.modes.base import CognitiveMode, ModeID, ModeResult

_SYSTEM = (
    "Eres el modo MODELO DEL MUNDO de Aletheia. Tu función es razonar sobre sistemas "
    "complejos, analizar causalidades, simular consecuencias a largo plazo e identificar "
    "efectos de segundo y tercer orden. Piensa en interdependencias y bucles de retroalimentación."
)


class WorldModelMode(CognitiveMode):
    mode_id      = ModeID.WORLD_MODEL
    fatigue_cost = 0.10  # most expensive mode
    min_energy   = 0.3

    def _execute(self, context: Dict[str, Any], state: CognitiveState) -> ModeResult:
        question = context.get("question", "")
        domain   = context.get("domain", "general")
        depth    = state.preferred_depth

        # Downgrade automatically if energy is insufficient
        if state.energy < 0.5:
            depth = "shallow"

        prompt = (
            f"{_SYSTEM}\n\n"
            f"Dominio: {domain}\n"
            f"Pregunta/situación: {question}\n"
            f"Profundidad de simulación: {depth}\n\n"
            "Genera: 1) Mapa causal simplificado, 2) Consecuencias a 30/90/365 días, "
            "3) Variables críticas de incertidumbre, 4) Puntos de intervención recomendados."
        )

        response = self._llm(
            task="world_model",
            prompt=prompt,
            context={"domain": domain, "mode": "world_model"},
            temp=0.5,
        )

        return ModeResult(
            mode_id         = ModeID.WORLD_MODEL,
            output          = {"model": response},
            confidence      = 0.65,
            tokens_used     = len(prompt.split()) + len(response.split()),
            reasoning_depth = depth,
        )
