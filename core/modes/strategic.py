"""
STRATEGIC mode — long-term planning, prioritisation, trade-off analysis.
"""

from __future__ import annotations

from typing import Any, Dict

from core.cognitive_state import CognitiveState
from core.modes.base import CognitiveMode, ModeID, ModeResult

_SYSTEM = (
    "Eres el modo ESTRATÉGICO de Aletheia. Tu función es pensar a largo plazo, "
    "priorizar objetivos, analizar escenarios y alinear decisiones con metas vitales. "
    "Considera trade-offs reales, preserva opcionalidad y evita el pensamiento táctico miope."
)


class StrategicMode(CognitiveMode):
    mode_id      = ModeID.STRATEGIC
    fatigue_cost = 0.08
    min_energy   = 0.2

    def _execute(self, context: Dict[str, Any], state: CognitiveState) -> ModeResult:
        question = context.get("question", "")
        domain   = context.get("domain", "general")
        memory   = context.get("memory", [])

        memory_str = _summarise_memory(memory, limit=5)
        depth = state.preferred_depth

        prompt = (
            f"{_SYSTEM}\n\n"
            f"Contexto previo: {memory_str}\n"
            f"Dominio: {domain}\n"
            f"Solicitud: {question}\n\n"
            f"Profundidad: {depth}. "
            "Genera: 1) Objetivo central, 2) Escenarios posibles (optimista/conservador/pesimista), "
            "3) Trade-offs clave, 4) Próximos pasos priorizados."
        )

        response = self._llm(
            task="strategic",
            prompt=prompt,
            context={"domain": domain, "mode": "strategic"},
            temp=0.4,
        )

        return ModeResult(
            mode_id         = ModeID.STRATEGIC,
            output          = {"plan": response},
            confidence      = 0.7,
            tokens_used     = len(prompt.split()) + len(response.split()),
            reasoning_depth = depth,
        )


def _summarise_memory(memory: list, limit: int = 5) -> str:
    if not memory:
        return "(sin memoria previa)"
    items = memory[-limit:]
    return "; ".join(str(m)[:80] for m in items)
