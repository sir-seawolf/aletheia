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

from core.llm.provider_ranker import best_provider

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
    provider:    str    # "ollama" | "claude" | "openai" | "deepseek" | "groq" | "mistral" | "openrouter" | "mock"
    model_tier:  str    # "local" | "free" | "premium"
    temperature: float
    max_tokens:  int
    reasoning:   str    # human-readable explanation
    use_cache:   bool = True
    skip_llm:    bool = False  # True → use deterministic path, bypass LLM


def _best_free_provider() -> Optional[str]:
    """Return the best available free-cloud provider, or None if none configured."""
    import os
    try:
        from core.config.preferences import load as _load
        prefs  = _load()
        stored = prefs.get("llm", {}).get("api_key", "")
        stored_provider = prefs.get("llm", {}).get("provider", "ollama")
        # If the configured provider is already a free-tier cloud, use it
        if stored_provider in ("groq", "openrouter", "deepseek", "mistral") and stored:
            return stored_provider
    except Exception:
        pass
    # Fallback: check env vars in preference order
    for pname, env in (("groq", "GROQ_API_KEY"), ("openrouter", "OPENROUTER_API_KEY"),
                       ("deepseek", "DEEPSEEK_API_KEY"), ("mistral", "MISTRAL_API_KEY")):
        if os.getenv(env, ""):
            return pname
    return None


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
        early = (
            self._tier0_deterministic(task)
            or self._tier_privacy(context)
            or self._tier1_critical(state)
            or self._tier2_fatigue(state, preferred_provider)
            or self._tier3_latency(state)
        )
        if early:
            return early

        complexity    = _TASK_COMPLEXITY.get(task, 0.5)
        learned       = self._learned_provider(task, state)
        premium       = self._tier4_premium(complexity, state, preferred_provider, learned)
        return premium or self._tier5_balanced(state, preferred_provider, learned)

    # ── Tier helpers (each returns RouteDecision or None) ────────────────────

    @staticmethod
    def _tier0_deterministic(task: str) -> Optional[RouteDecision]:
        if task not in _DETERMINISTIC_TASKS:
            return None
        return RouteDecision(
            provider="deterministic", model_tier="local",
            temperature=0.0, max_tokens=0,
            reasoning=f"task '{task}' is deterministic",
            skip_llm=True,
        )

    @staticmethod
    def _tier_privacy(context: Dict[str, Any]) -> Optional[RouteDecision]:
        if not RoutingIntelligence._is_sensitive(context):
            return None
        return RouteDecision(
            provider="ollama", model_tier="local",
            temperature=0.2, max_tokens=1024,
            reasoning="privacy: sensitive data detected → local only",
            use_cache=False,
        )

    @staticmethod
    def _tier1_critical(state: CognitiveState) -> Optional[RouteDecision]:
        if not state.is_critical:
            return None
        return RouteDecision(
            provider="ollama", model_tier="local",
            temperature=0.1, max_tokens=256,
            reasoning=f"critical: fatigue={state.fatigue:.2f} or budget={state.token_budget}",
            use_cache=True,
        )

    @staticmethod
    def _tier2_fatigue(state: CognitiveState, preferred: Optional[str]) -> Optional[RouteDecision]:
        if state.fatigue <= 0.6:
            return None
        return RouteDecision(
            provider=preferred or "ollama", model_tier="local",
            temperature=0.2, max_tokens=800,
            reasoning=f"fatigue={state.fatigue:.2f}: local routing",
            use_cache=True,
        )

    @staticmethod
    def _tier3_latency(state: CognitiveState) -> Optional[RouteDecision]:
        if state.latency_tolerance >= 0.3:
            return None
        return RouteDecision(
            provider="ollama", model_tier="local",
            temperature=0.3, max_tokens=600,
            reasoning=f"latency_tolerance={state.latency_tolerance:.2f}: fast local",
            use_cache=True,
        )

    @staticmethod
    def _learned_provider(task: str, state: CognitiveState) -> Optional[str]:
        try:
            from core.cognition.trace_learner import trace_learner
            return trace_learner.recommend_provider(task, state)
        except Exception:
            return None

    @staticmethod
    def _tier4_premium(
        complexity: float, state: CognitiveState,
        preferred: Optional[str], learned: Optional[str],
    ) -> Optional[RouteDecision]:
        if not (complexity >= 0.7 and state.energy > 0.7
                and state.token_budget > 2_000 and state.fatigue < 0.4):
            return None
        provider = preferred or learned or "claude"
        reason   = f"complexity={complexity:.1f}, energy={state.energy:.2f} → premium"
        if learned:
            reason += f" (learned:{learned})"
        return RouteDecision(
            provider=provider, model_tier="premium",
            temperature=0.3 + complexity * 0.2,
            max_tokens=min(4_000, state.token_budget // 2),
            reasoning=reason,
            use_cache=complexity < 0.85,
        )

    @staticmethod
    def _tier5_balanced(
        state: CognitiveState,
        preferred: Optional[str],
        learned: Optional[str],
    ) -> RouteDecision:
        policy = "fastest"
        try:
            from core.config.preferences import load as _load
            policy = _load().get("llm", {}).get("routing_policy", "fastest")
        except Exception:
            pass

        ranked_best = best_provider(policy=policy)
        free_cloud = _best_free_provider()
        provider = preferred or learned or ranked_best or free_cloud or "ollama"
        tier = "free" if provider != "ollama" else "local"
        reason = f"default balanced routing (policy:{policy})"
        if learned:
            reason += f" (learned:{learned})"
        elif ranked_best and provider == ranked_best:
            reason += f" (ranked:{ranked_best})"
        elif free_cloud and provider == free_cloud:
            reason += f" (free-cloud:{free_cloud})"
        return RouteDecision(
            provider=provider, model_tier=tier,
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
