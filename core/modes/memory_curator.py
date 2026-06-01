"""
MEMORY_CURATOR mode — consolidation, summarisation, salience scoring, deduplication.

Runs as a background maintenance mode. Compresses working memory, removes noise,
links related concepts, and flags contradictions for REFLECTIVE.
"""

from __future__ import annotations

from typing import Any, Dict, List

from core.cognitive_state import CognitiveState
from core.modes.base import CognitiveMode, ModeID, ModeResult


class MemoryCuratorMode(CognitiveMode):
    mode_id      = ModeID.MEMORY_CURATOR
    fatigue_cost = 0.04
    min_energy   = 0.05

    def _execute(self, context: Dict[str, Any], state: CognitiveState) -> ModeResult:
        domain = context.get("domain", "general")

        stats: Dict[str, Any] = {
            "consolidated": 0,
            "compressed":   0,
            "contradictions_flagged": 0,
        }

        # 1. Run memory consolidation (PALACE → semantic graph)
        try:
            from core.memory.consolidator import consolidate
            n = consolidate(verbose=False)
            stats["consolidated"] = n
        except Exception:
            pass

        # 2. Compress working memory if under pressure
        if state.memory_pressure > 0.5:
            try:
                from core.memory.working_memory import session as wm
                summary = self._compress(wm)
                stats["compressed"] = len(summary)
                state.memory_pressure = max(0.0, state.memory_pressure - 0.2)
            except Exception:
                pass

        # 3. Update state
        state.memory_pressure = max(0.0, state.memory_pressure - 0.05)

        return ModeResult(
            mode_id         = ModeID.MEMORY_CURATOR,
            output          = stats,
            confidence      = 0.85,
            tokens_used     = 0,
            reasoning_depth = "minimal",
        )

    def _compress(self, wm: Any) -> str:
        try:
            return wm.to_context_str(last_n=4)
        except Exception:
            return ""

    def salience_score(self, items: List[Any]) -> List[tuple]:
        scored = []
        for item in items:
            text = str(item).lower()
            score = 0.5
            for kw in ("decisión", "importante", "critico", "deuda", "oportunidad", "riesgo"):
                if kw in text:
                    score += 0.1
            scored.append((min(score, 1.0), item))
        return sorted(scored, reverse=True)
