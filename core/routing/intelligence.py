"""
RoutingIntelligence — dynamic provider routing for Aletheia.

Priority hierarchy (hard order, not tunable):
  1. Deterministic logic      — no LLM needed
  2. Local / offline (Ollama) — privacy + cost
  3. Free / open cloud        — open models
  4. Premium reasoning models — best quality

Routing factors: task complexity, privacy sensitivity, CognitiveState
(fatigue, energy, token budget, latency tolerance), and explicit overrides.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Set

from core.cognitive_state import CognitiveState


# Tasks that are always handled deterministically — never call an LLM
_DETERMINISTIC_TASKS: Set[str] = {
    "classification", "filtering", "routing", "scoring",
    "deduplication", "hashing", "templating",
}

# Approximate complexity of each task type (0.0 = trivial, 1.0 = maximum)
_TASK_COMPLEXITY: Dict[str, float] = {
    "chat":                0.3,
    "exploration":         0.6,
    "analytical":          0.65,
    "strategic":           0.7,
    "creative":            0.6,
    "reflective":          0.55,
    "research":            0.65,
    "simulation":          0.75,
    "kronos_analysis":     0.8,
    "world_model":         0.9,
    "cognitive_execution": 0.85,
}

# Keywords that force local routing regardless of everything else
_PRIVACY_TRIGGERS: Set[str] = {
    "dni", "nif", "passport", "contraseña", "password",
    "pin", "iban", "api key", "token", "secret", "credential",
}


@dataclass
class RouteDecision:
    provider:    str    # "ollama" | "claude" | "openai" | "deepseek" | "groq" | "mistral" | "mock"
    model_tier:  str    # "local" | "free" | "premium"
    temperature: float
    max_tokens:  int
    reasoning:   str    # human-readable explanation
    use_cache:   bool = True
    skip_llm:    bool = False  # True → use deterministic path, bypass LLM


class RoutingIntelligence:
    """
    Stateless routing engine. Call decide() before every LLM call.
    Reads CognitiveState but never mutates it.
    """

    def decide(
        self,
        task: str,
        context: Dict[str, Any],
        state: CognitiveState,
        preferred_provider: Optional[str] = None,
    ) -> RouteDecision:

        # ── Tier 0: deterministic — no LLM ever ────────────────────────────
        if task in _DETERMINISTIC_TASKS:
            return RouteDecision(
                provider="deterministic", model_tier="local",
                temperature=0.0, max_tokens=0,
                reasoning=f"task '{task}' is deterministic",
                skip_llm=True,
            )

        # ── Privacy check — always local ────────────────────────────────────
        if self._is_sensitive(context):
            return RouteDecision(
                provider="ollama", model_tier="local",
                temperature=0.2, max_tokens=1024,
                reasoning="privacy: sensitive data detected → local only",
                use_cache=False,
            )

        # ── Tier 1: critical state — cheapest local path ────────────────────
        if state.is_critical:
            return RouteDecision(
                provider="ollama", model_tier="local",
                temperature=0.1, max_tokens=256,
                reasoning=f"critical: fatigue={state.fatigue:.2f} or budget={state.token_budget}",
                use_cache=True,
            )

        # ── Tier 2: high fatigue — local preferred ──────────────────────────
        if state.fatigue > 0.6:
            return RouteDecision(
                provider=preferred_provider or "ollama", model_tier="local",
                temperature=0.2, max_tokens=800,
                reasoning=f"fatigue={state.fatigue:.2f}: local routing",
                use_cache=True,
            )

        # ── Tier 3: voice / low-latency mode ───────────────────────────────
        if state.latency_tolerance < 0.3:
            return RouteDecision(
                provider="ollama", model_tier="local",
                temperature=0.3, max_tokens=600,
                reasoning=f"latency_tolerance={state.latency_tolerance:.2f}: fast local",
                use_cache=True,
            )

        # ── Tier 3.5: TraceLearner learned provider preference ─────────────
        complexity = _TASK_COMPLEXITY.get(task, 0.5)
        learned_provider: Optional[str] = None
        try:
            from core.cognition.trace_learner import trace_learner
            learned_provider = trace_learner.recommend_provider(task, state)
        except Exception:
            pass

        # ── Tier 4: complex + healthy → premium ────────────────────────────
        if (complexity >= 0.7
                and state.energy > 0.7
                and state.token_budget > 2_000
                and state.fatigue < 0.4):
            provider = preferred_provider or learned_provider or "claude"
            reason = f"complexity={complexity:.1f}, energy={state.energy:.2f} → premium"
            if learned_provider:
                reason += f" (learned:{learned_provider})"
            return RouteDecision(
                provider=provider, model_tier="premium",
                temperature=0.3 + complexity * 0.2,
                max_tokens=min(4_000, state.token_budget // 2),
                reasoning=reason,
                use_cache=complexity < 0.85,
            )

        # ── Tier 5: default balanced (learned provider if available) ────────
        provider = preferred_provider or learned_provider or "ollama"
        reason = "default balanced routing"
        if learned_provider:
            reason += f" (learned:{learned_provider})"
        return RouteDecision(
            provider=provider, model_tier="free",
            temperature=0.3,
            max_tokens=min(2_000, state.token_budget),
            reasoning=reason,
            use_cache=True,
        )

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _is_sensitive(context: Dict[str, Any]) -> bool:
        text = str(context).lower()
        return any(kw in text for kw in _PRIVACY_TRIGGERS)

    def tier_for_state(self, state: CognitiveState) -> str:
        """Quick lookup without a full decision — used by FatigueEngine."""
        if state.is_critical:
            return "local"
        if state.fatigue > 0.6:
            return "local"
        if state.fatigue > 0.4:
            return "free"
        return "premium"


# Singleton
routing_intelligence = RoutingIntelligence()
