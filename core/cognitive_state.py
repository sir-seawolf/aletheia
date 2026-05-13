"""
CognitiveState — shared runtime state for the Aletheia cognitive OS.

Single source of truth for energy, fatigue, focus, token budget, and confidence.
All cognitive modes and the routing engine read from this state.
Per-session instances are managed by SessionStateRegistry (session_state.py).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class CognitiveState:
    # Core vitals (0.0–1.0 unless noted)
    energy: float = 1.0            # overall system vitality; decreases with fatigue
    coherence: float = 1.0         # internal consistency of reasoning chain
    focus: float = 1.0             # attention depth; drops under memory pressure
    token_budget: int = 8_000      # remaining tokens available for this session
    memory_pressure: float = 0.0   # load on working/semantic memory
    fatigue: float = 0.0           # accumulated cognitive cost
    confidence: float = 0.8        # self-assessed quality of last answer
    latency_tolerance: float = 1.0 # 0=fast required (voice), 1=quality preferred

    # Internal counters — not serialised to LLM prompts
    _llm_calls: int = field(default=0, repr=False)
    _total_tokens_used: int = field(default=0, repr=False)
    _session_start: float = field(default_factory=time.time, repr=False)

    # ── Derived properties ──────────────────────────────────────────────────

    @property
    def is_fatigued(self) -> bool:
        return self.fatigue > 0.6

    @property
    def is_critical(self) -> bool:
        return self.fatigue > 0.85 or self.token_budget < 300

    @property
    def preferred_depth(self) -> str:
        if self.is_critical:
            return "minimal"
        if self.fatigue > 0.6:
            return "shallow"
        if self.energy > 0.8 and self.coherence > 0.8:
            return "deep"
        return "normal"

    @property
    def preferred_model_tier(self) -> str:
        """local | free | premium — informs RoutingIntelligence."""
        if self.is_critical or self.fatigue > 0.7:
            return "local"
        if self.fatigue > 0.4:
            return "free"
        return "premium"

    def can_afford_mode(self, mode_weight: float = 0.06) -> bool:
        """True if the system has enough energy to activate a mode at given cost."""
        return self.energy >= mode_weight and not self.is_critical

    # ── Mutators ────────────────────────────────────────────────────────────

    def record_llm_call(self, tokens_used: int = 0) -> None:
        self._llm_calls += 1
        self._total_tokens_used += tokens_used
        self.token_budget = max(0, self.token_budget - tokens_used)

    def apply_fatigue_delta(self, delta: float) -> None:
        self.fatigue = min(1.0, max(0.0, self.fatigue + delta))
        self.energy = max(0.0, 1.0 - self.fatigue * 0.8)
        self.focus = max(0.0, 1.0 - self.memory_pressure * 0.6 - self.fatigue * 0.4)

    def recover(self, rate: float = 0.05) -> None:
        self.fatigue = max(0.0, self.fatigue - rate)
        self.energy = min(1.0, self.energy + rate * 0.5)
        self.memory_pressure = max(0.0, self.memory_pressure - rate * 0.3)

    def update_coherence(self, score: float) -> None:
        self.coherence = self.coherence * 0.7 + score * 0.3

    def update_confidence(self, score: float) -> None:
        self.confidence = self.confidence * 0.6 + score * 0.4

    # ── Serialisation ────────────────────────────────────────────────────────

    def snapshot(self) -> Dict[str, Any]:
        return {
            "energy":            round(self.energy, 3),
            "coherence":         round(self.coherence, 3),
            "focus":             round(self.focus, 3),
            "token_budget":      self.token_budget,
            "memory_pressure":   round(self.memory_pressure, 3),
            "fatigue":           round(self.fatigue, 3),
            "confidence":        round(self.confidence, 3),
            "latency_tolerance": round(self.latency_tolerance, 3),
            "preferred_depth":   self.preferred_depth,
            "model_tier":        self.preferred_model_tier,
            "llm_calls":         self._llm_calls,
        }

    def __repr__(self) -> str:
        return (
            f"CognitiveState(fatigue={self.fatigue:.2f}, energy={self.energy:.2f}, "
            f"coherence={self.coherence:.2f}, budget={self.token_budget}, "
            f"depth={self.preferred_depth})"
        )
