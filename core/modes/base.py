"""
CognitiveMode — base contract for all Aletheia cognitive modes.

All modes share the same memory, tools, identity, and contextual bus.
They differ only in heuristics, priorities, reasoning style, risk tolerance,
depth, and tool preferences.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from core.cognitive_state import CognitiveState


class ModeID(str, Enum):
    OBSERVER       = "OBSERVER"
    ANALYTICAL     = "ANALYTICAL"
    STRATEGIC      = "STRATEGIC"
    KRONOS         = "KRONOS"
    CREATIVE       = "CREATIVE"
    REFLECTIVE     = "REFLECTIVE"
    GUARDIAN       = "GUARDIAN"
    EXECUTIVE      = "EXECUTIVE"
    MEMORY_CURATOR = "MEMORY_CURATOR"
    RESEARCHER     = "RESEARCHER"
    WORLD_MODEL    = "WORLD_MODEL"


@dataclass
class ModeResult:
    mode_id: ModeID
    output: Dict[str, Any]
    confidence: float
    tokens_used: int = 0
    reasoning_depth: str = "normal"
    next_mode: Optional[ModeID] = None        # single-mode routing suggestion
    next_blend: Optional[Any] = None          # ModeBlend — checked before next_mode
    events: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        blend_dict = None
        if self.next_blend is not None:
            try:
                blend_dict = self.next_blend.to_dict()
            except Exception:
                pass
        return {
            "mode":            self.mode_id.value,
            "output":          self.output,
            "confidence":      round(self.confidence, 3),
            "tokens_used":     self.tokens_used,
            "reasoning_depth": self.reasoning_depth,
            "next_mode":       self.next_mode.value if self.next_mode else None,
            "next_blend":      blend_dict,
        }


class CognitiveMode(ABC):
    """
    Abstract base for all Aletheia cognitive modes.

    Subclasses set class-level `mode_id`, `fatigue_cost`, and `min_energy`,
    then implement `_execute()`.
    """

    mode_id: ModeID
    fatigue_cost: float = 0.05   # fatigue added per activation
    min_energy: float = 0.05     # minimum energy required

    def can_activate(self, state: CognitiveState) -> bool:
        return state.energy >= self.min_energy and not state.is_critical

    def activate(self, context: Dict[str, Any], state: CognitiveState) -> ModeResult:
        """Entry point. Applies fatigue accounting after _execute."""
        result = self._execute(context, state)
        state.apply_fatigue_delta(self.fatigue_cost)
        state.record_llm_call(result.tokens_used)
        return result

    @abstractmethod
    def _execute(self, context: Dict[str, Any], state: CognitiveState) -> ModeResult:
        ...

    # ── Shared utilities available to all modes ─────────────────────────────

    def context_summary(self, context: Dict[str, Any], state: CognitiveState) -> str:
        domain   = context.get("domain", "unknown")
        question = context.get("question", "")[:120]
        return f"[{self.mode_id.value}|depth={state.preferred_depth}] {domain}: {question}"

    def _llm(self, task: str, prompt: str, context: Dict[str, Any],
             temp: float = 0.3) -> str:
        from core.llm.router import router
        return router.generate(task=task, prompt=prompt, context=context, temp=temp)
