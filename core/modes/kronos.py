"""
KRONOS mode — financial reasoning, sustainability, resilience, resource optimisation.

Philosophy: money is stored energy and future decision capacity.
Optimise life sustainability, not only income. Preserve resilience and optionality.

Delegates to core.kronos.analyzer for the actual analysis.
"""

from __future__ import annotations

from typing import Any, Dict

from core.cognitive_state import CognitiveState
from core.modes.base import CognitiveMode, ModeID, ModeResult


class KronosMode(CognitiveMode):
    mode_id      = ModeID.KRONOS
    fatigue_cost = 0.06
    min_energy   = 0.1

    def _execute(self, context: Dict[str, Any], state: CognitiveState) -> ModeResult:
        question = context.get("question", "")
        depth    = state.preferred_depth

        try:
            from core.kronos.analyzer import quick_analysis, full_analysis
            if depth in ("minimal", "shallow") or state.latency_tolerance < 0.4:
                response = quick_analysis(question)
                used_depth = "shallow"
            else:
                response = full_analysis(question)
                used_depth = "deep"
        except Exception as exc:
            response = f"[KRONOS] Error en análisis financiero: {exc}"
            used_depth = "error"

        return ModeResult(
            mode_id         = ModeID.KRONOS,
            output          = {"analysis": response},
            confidence      = 0.8,
            tokens_used     = len(response.split()),
            reasoning_depth = used_depth,
        )
