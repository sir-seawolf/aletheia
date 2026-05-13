"""
FatigueEngine — adaptive fatigue tracking for Aletheia cognitive OS.

Fatigue increases with:
  - LLM calls (cost proportional to provider tier)
  - Guardian blocks (indicates reasoning errors)
  - Context overflows / token budget violations
  - High memory pressure
  - Pipeline errors
  - Recursive / redundant calls

When fatigued, Aletheia:
  - Reduces reasoning depth
  - Compresses context more aggressively
  - Prefers local/cheap models
  - Postpones expensive tasks
  - Asks for clarification earlier
  - Reduces max recursion depth

Recovery occurs on successful completions and idle periods.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from core.cognitive_state import CognitiveState


# Fatigue cost per event type
_COSTS: Dict[str, float] = {
    "llm_call_local":       0.02,
    "llm_call_free":        0.04,
    "llm_call_premium":     0.07,
    "guardian_block":       0.10,
    "context_overflow":     0.12,
    "token_budget_low":     0.06,
    "memory_pressure_high": 0.05,
    "pipeline_error":       0.15,
    "recursive_call":       0.10,
    "timeout":              0.08,
}

# Tier → event type mapping for LLM calls
_TIER_EVENT: Dict[str, str] = {
    "local":   "llm_call_local",
    "free":    "llm_call_free",
    "premium": "llm_call_premium",
}

# Recovery rates
_RECOVERY_SUCCESS: float = 0.06
_RECOVERY_IDLE:    float = 0.03


@dataclass
class FatigueEvent:
    timestamp:      float
    cause:          str
    delta:          float
    fatigue_after:  float
    session_id:     str = "local"


class FatigueEngine:

    def __init__(self) -> None:
        self._history: List[FatigueEvent] = []
        self._last_call: float = time.time()

    # ── Recording ────────────────────────────────────────────────────────────

    def record(
        self,
        event_type: str,
        state: CognitiveState,
        session_id: str = "local",
    ) -> float:
        """
        Apply fatigue delta for event_type. Returns the delta applied.
        Fatigue compounds: already-fatigued systems pay extra.
        """
        base_cost = _COSTS.get(event_type, 0.02)

        # Compounding: fatigue above 0.5 amplifies further costs
        if state.fatigue > 0.5:
            base_cost *= 1.0 + (state.fatigue - 0.5)

        state.apply_fatigue_delta(base_cost)

        # Memory pressure tracks fatigue with some lag
        state.memory_pressure = min(1.0, state.memory_pressure + base_cost * 0.4)

        self._history.append(FatigueEvent(
            timestamp=time.time(),
            cause=event_type,
            delta=base_cost,
            fatigue_after=state.fatigue,
            session_id=session_id,
        ))
        self._last_call = time.time()
        return base_cost

    def record_llm_call(
        self,
        model_tier: str,
        state: CognitiveState,
        session_id: str = "local",
    ) -> float:
        event = _TIER_EVENT.get(model_tier, "llm_call_local")
        before = state.fatigue
        delta = self.record(event, state, session_id)
        # Write fatigue snapshot to active trace (best-effort)
        try:
            from core.tracing.context import trace_fatigue
            trace_fatigue(before, state.fatigue)
        except Exception:
            pass
        return delta

    def recover(
        self,
        state: CognitiveState,
        reason: str = "idle",
        session_id: str = "local",
    ) -> None:
        rate = _RECOVERY_SUCCESS if reason == "success" else _RECOVERY_IDLE
        state.recover(rate)
        self._history.append(FatigueEvent(
            timestamp=time.time(),
            cause=f"recovery:{reason}",
            delta=-rate,
            fatigue_after=state.fatigue,
            session_id=session_id,
        ))

    # ── Adaptations ──────────────────────────────────────────────────────────

    def get_adaptations(self, state: CognitiveState) -> Dict[str, Any]:
        """
        Behavioural constraints derived from current fatigue level.
        Orchestrators and routers should respect these.
        """
        f = state.fatigue

        if f < 0.2:
            return {
                "reasoning_depth":           "deep",
                "context_compression":       "minimal",
                "prefer_local":              False,
                "max_recursion":             5,
                "ask_clarification_threshold": 0.15,
                "postpone_heavy_tasks":      False,
                "max_tokens_multiplier":     1.0,
            }
        if f < 0.4:
            return {
                "reasoning_depth":           "normal",
                "context_compression":       "moderate",
                "prefer_local":              False,
                "max_recursion":             3,
                "ask_clarification_threshold": 0.35,
                "postpone_heavy_tasks":      False,
                "max_tokens_multiplier":     0.8,
            }
        if f < 0.6:
            return {
                "reasoning_depth":           "shallow",
                "context_compression":       "aggressive",
                "prefer_local":              True,
                "max_recursion":             2,
                "ask_clarification_threshold": 0.5,
                "postpone_heavy_tasks":      False,
                "max_tokens_multiplier":     0.6,
            }
        if f < 0.85:
            return {
                "reasoning_depth":           "minimal",
                "context_compression":       "maximum",
                "prefer_local":              True,
                "max_recursion":             1,
                "ask_clarification_threshold": 0.7,
                "postpone_heavy_tasks":      True,
                "max_tokens_multiplier":     0.4,
            }
        # Critical
        return {
            "reasoning_depth":           "emergency",
            "context_compression":       "emergency",
            "prefer_local":              True,
            "max_recursion":             0,
            "ask_clarification_threshold": 1.0,
            "postpone_heavy_tasks":      True,
            "max_tokens_multiplier":     0.2,
        }

    def should_postpone(self, task_complexity: float, state: CognitiveState) -> bool:
        a = self.get_adaptations(state)
        return bool(a["postpone_heavy_tasks"]) and task_complexity > 0.6

    def should_ask_clarification(self, ambiguity: float, state: CognitiveState) -> bool:
        threshold = self.get_adaptations(state)["ask_clarification_threshold"]
        return ambiguity >= threshold

    def compress_context(
        self,
        items: List[Any],
        state: CognitiveState,
        max_items: int = 20,
    ) -> List[Any]:
        """
        Reduce context list according to current fatigue adaptations.
        Higher fatigue → keep fewer items.
        """
        a = self.get_adaptations(state)
        mode = a["context_compression"]
        limits = {
            "minimal":   max_items,
            "moderate":  max(5, max_items // 2),
            "aggressive": max(3, max_items // 4),
            "maximum":   3,
            "emergency": 1,
        }
        keep = limits.get(mode, max_items // 2)
        return items[-keep:] if len(items) > keep else items

    # ── Diagnostics ──────────────────────────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        if not self._history:
            return {"events": 0, "total_fatigue_applied": 0.0, "last_cause": None}
        total = sum(e.delta for e in self._history)
        return {
            "events":                len(self._history),
            "total_fatigue_applied": round(total, 4),
            "last_cause":            self._history[-1].cause,
            "last_fatigue":          round(self._history[-1].fatigue_after, 3),
        }

    def recent_events(self, n: int = 10) -> List[Dict[str, Any]]:
        return [
            {"cause": e.cause, "delta": round(e.delta, 4), "fatigue_after": round(e.fatigue_after, 3)}
            for e in self._history[-n:]
        ]


# Singleton
fatigue_engine = FatigueEngine()
