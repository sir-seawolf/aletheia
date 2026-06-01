"""
ACO v3 MetaCortex — session-level policy optimizer.

Maintains in-memory EMA success rates per mode/blend, updated on every
interaction via DQS (Decision Quality Score = ModeResult.confidence).
No persistence: resets on restart. Complements TraceLearner (cross-session).

Integration:
  - runtime.py        → meta_cortex.learn(mode, dqs)  after each v3 response
  - ObserverMode      → meta_cortex.recommend_*(domain, state) as Priority 0/1
  - /api/learning/*   → meta_cortex.stats() for dashboard visibility

Policy update: EMA with alpha=0.3, initialised at 0.5 (neutral).
Recommendation requires MIN_CALLS interactions before acting.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

MIN_CALLS = 3        # minimum interactions before a recommendation is made
MIN_SUCCESS = 0.55   # minimum EMA success_rate to recommend
EMA_ALPHA  = 0.3     # weight of latest observation in the EMA

_BLEND_PRESET_NAMES = {
    "strategic_analytical", "reflective_kronos", "creative_world",
    "analytical_reflective", "strategic_creative", "kronos_strategic",
}


@dataclass
class PolicyStats:
    success_rate: float = 0.5
    call_count:   int   = 0
    last_dqs:     float = 0.0

    def update(self, dqs: float) -> None:
        self.success_rate = (1 - EMA_ALPHA) * self.success_rate + EMA_ALPHA * dqs
        self.call_count  += 1
        self.last_dqs     = dqs

    def qualifies(self) -> bool:
        return self.call_count >= MIN_CALLS and self.success_rate >= MIN_SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success_rate": round(self.success_rate, 3),
            "call_count":   self.call_count,
            "last_dqs":     round(self.last_dqs, 3),
            "qualifies":    self.qualifies(),
        }


class MetaCortex:
    """Session-level cognitive policy optimizer."""

    def __init__(self) -> None:
        self._policy: Dict[str, PolicyStats] = {}
        self._lock   = threading.Lock()

    # ── Learning ──────────────────────────────────────────────────────────────

    def learn(self, mode_or_blend: str, dqs: float) -> None:
        """Record an interaction outcome. dqs ∈ [0.0, 1.0]."""
        if not mode_or_blend:
            return
        dqs = max(0.0, min(1.0, dqs))
        with self._lock:
            self._policy.setdefault(mode_or_blend, PolicyStats()).update(dqs)

    # ── Recommendations ───────────────────────────────────────────────────────

    def recommend_mode(self, state: Any = None) -> Optional[str]:
        """
        Return the single mode (non-blend) with the highest EMA success_rate
        this session. Returns None if no qualified candidate exists.
        """
        with self._lock:
            candidates = [
                (name, s)
                for name, s in self._policy.items()
                if name not in _BLEND_PRESET_NAMES and s.qualifies()
            ]
        if not candidates:
            return None

        # Exclude heavy modes when fatigued
        if state is not None:
            try:
                heavy = {"WORLD_MODEL", "EXECUTIVE"}
                if getattr(state, "fatigue", 0) > 0.6:
                    candidates = [(n, s) for n, s in candidates if n not in heavy]
            except Exception:
                pass

        if not candidates:
            return None
        best = max(candidates, key=lambda x: x[1].success_rate)
        return best[0]

    def recommend_blend(self, state: Any = None) -> Optional[str]:
        """
        Return the blend preset with the highest EMA success_rate this session.
        Only when state has enough energy (energy > 0.5).
        """
        if state is not None:
            try:
                if getattr(state, "energy", 1.0) <= 0.5:
                    return None
            except Exception:
                pass

        with self._lock:
            candidates = [
                (name, s)
                for name, s in self._policy.items()
                if name in _BLEND_PRESET_NAMES and s.qualifies()
            ]
        if not candidates:
            return None
        best = max(candidates, key=lambda x: x[1].success_rate)
        return best[0]

    # ── Inspection ────────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                name: s.to_dict()
                for name, s in sorted(
                    self._policy.items(),
                    key=lambda x: -x[1].success_rate,
                )
            }

    def top_modes(self, n: int = 5) -> List[Dict[str, Any]]:
        with self._lock:
            ranked = sorted(
                self._policy.items(),
                key=lambda x: (-x[1].success_rate, -x[1].call_count),
            )
        return [
            {"mode": name, **s.to_dict()}
            for name, s in ranked[:n]
        ]

    def reset(self) -> None:
        with self._lock:
            self._policy.clear()

    def total_interactions(self) -> int:
        with self._lock:
            return sum(s.call_count for s in self._policy.values())


# Session singleton — shared across all requests in this process
meta_cortex = MetaCortex()
