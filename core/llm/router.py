"""
LLMRouter - Central LLM interface for Aletheia cognitive stack.

STATUS: IMPLEMENTED (production v1.2)
Dependencies: core.llm.providers.*, core.llm.cache, core.cognition.*, core.ecosystem.*, memory.service, core.palace.search
Last stable version: v1.2

v1.2 changes: RoutingIntelligence + FatigueEngine integrated into generate().
Full stack: Universe → Civilization → Ecosystem → Genome → SOI → Economy → ACL → SelfAware → Prefrontal → Cache + Palace.

Public API:
- generate(task: str, prompt: str, context: Optional[Dict[str, Any]] = None, temp: float = 0.3) → str
  Example correct: router.generate("exploration", "What is best?", {"domain": "finance"})
  Example incorrect: router.generate("exploration", "What is best?")  # Missing context breaks cache
"""

from typing import Optional, Dict, Any
from core.llm.providers.ollama import OllamaProvider
from core.llm.providers.mock import MockProvider
from core.llm.cache import LLMCacheV2
from core.learning.evaluator import ResponseEvaluator
from core.llm.learning_loop import LearningLoop
from core.palace.search import PalaceSearchEngine
from memory.service import retrieve_context
from core.cognition.prefrontal_controller import PrefrontalController
from core.cognition.self_awareness import SelfAwareLoop
from core.cognition.autonomous_layer import AutonomousCognitionLayer
from core.economy.cognitive_economy import CognitiveEconomy
from core.soi.self_optimizer import SelfOptimizingIntelligence
from core.genome.cognitive_genome import CognitiveGenome
from core.ecosystem.cognitive_ecosystem import CognitiveEcosystem
from core.civilization.self_aware_civilization import SelfAwareCivilization
from core.universe.reflexive_universe import ReflexiveUniverse


class LLMRouter:

    def __init__(self):
        self.ollama = OllamaProvider()
        self.mock = MockProvider()
        self.cache = LLMCacheV2()
        self.evaluator = ResponseEvaluator()
        self.learning = LearningLoop()
        self.palace_search = PalaceSearchEngine()

        # Full Ruta Aletheia Stack v1
        self.acl = AutonomousCognitionLayer()
        self.economy = CognitiveEconomy()
        self.prefrontal = PrefrontalController()
        self.self_awareness = SelfAwareLoop()
        self.optimizer = SelfOptimizingIntelligence(self.economy, self.acl, self)
        self.genome = CognitiveGenome()
        self.ecosystem = CognitiveEcosystem(self, retrieve_context, self.palace_search, self.economy)
        self.civilization = SelfAwareCivilization(self.ecosystem, self.genome, self.economy, self.palace_search)
        self.universe = ReflexiveUniverse(self.civilization)

    def generate(self, task: str, prompt: str, context: Optional[Dict[str, Any]] = None,
                 temp: float = 0.3, agent_id: Optional[str] = None) -> str:
        """
        Generate LLM response through full cognitive stack with caching.

        Provider priority (v1.2 — RoutingIntelligence-aware):
          0. CognitiveState gate — skip or downgrade if fatigued/critical
          1. Per-agent override (agent_id key in preferences.llm.agents)
          2. RoutingIntelligence decision (fatigue, latency, privacy, complexity)
          3. Global preference file / env var (claude, openai, ollama)
          4. Ollama local if no preference set
          5. Mock fallback if all providers fail
        """
        ctx      = context or {}
        session  = ctx.get("session_id", "local")
        use_cache = task not in ("chat", "kronos_voice")

        # ── CognitiveState + RoutingIntelligence ────────────────────────────
        route_provider: Optional[str] = None
        model_tier = "local"
        try:
            from core.session_state import get_state
            from core.routing.intelligence import routing_intelligence
            state = get_state(session)
            decision = routing_intelligence.decide(task, ctx, state, preferred_provider=None)
            model_tier = decision.model_tier
            if decision.skip_llm:
                return self.mock.generate(prompt)
            if not decision.use_cache:
                use_cache = False
            if decision.provider not in ("deterministic", "ollama"):
                route_provider = decision.provider
            elif decision.provider == "ollama":
                route_provider = "ollama"
            # Write routing decision to active trace (best-effort)
            try:
                from core.tracing.context import trace_routing
                trace_routing(decision.provider, decision.model_tier, decision.reasoning)
            except Exception:
                pass
        except Exception:
            pass

        if use_cache:
            cached = self.cache.get(task, prompt, ctx)
            if cached:
                return cached

        # TURBO mode
        try:
            from core.turbo.mode import turbo_mode
            if turbo_mode.is_active():
                from core.turbo.panel import turbo_panel
                response = turbo_panel.run(task, prompt, temp)
                self.learning.process(task, prompt, response, {"score": 0.9, "retry": False}, ctx)
                if use_cache:
                    self.cache.set(task, prompt, ctx, response)
                return response
        except Exception:
            pass

        try:
            response = self._call_configured(
                prompt, temp, agent_id=agent_id, route_provider=route_provider,
            )
            if not response or response.startswith("[ERROR]"):
                response = self.mock.generate(prompt)
        except Exception:
            response = self.mock.generate(prompt)
            # Record pipeline error fatigue
            try:
                from core.session_state import get_state
                from core.fatigue.engine import fatigue_engine
                fatigue_engine.record("pipeline_error", get_state(session), session)
            except Exception:
                pass

        # ── Post-call fatigue accounting ────────────────────────────────────
        try:
            from core.session_state import get_state
            from core.fatigue.engine import fatigue_engine
            fatigue_engine.record_llm_call(model_tier, get_state(session), session)
        except Exception:
            pass

        self.learning.process(task, prompt, response, {"score": 0.9, "retry": False}, ctx)
        if use_cache:
            self.cache.set(task, prompt, ctx, response)

        return response

    def _call_configured(self, prompt: str, temp: float,
                         agent_id: Optional[str] = None,
                         route_provider: Optional[str] = None) -> str:
        """
        Route to the configured provider, then walk the failover chain on error.
        Per-agent overrides > route_provider hint > global preference.
        """
        primary, chain, _get_key = "ollama", [], lambda _: ""
        try:
            from core.config.preferences import (
                get_llm_provider, get_api_key, get_failover_chain,
                get_provider_for_agent,
            )
            primary   = get_provider_for_agent(agent_id) if agent_id else get_llm_provider()
            chain     = get_failover_chain()
            _get_key  = get_api_key
        except Exception:
            pass

        # RoutingIntelligence hint overrides global pref (but agent override still wins)
        if route_provider and not agent_id:
            primary = route_provider

        candidates = [{"provider": primary}] + list(chain)

        last_exc: Exception | None = None
        for entry in candidates:
            pname = entry.get("provider", "ollama")
            key   = entry.get("api_key", "") or (_get_key(pname) if pname != "ollama" else "")
            try:
                result = self._call_provider(pname, key, prompt, temp)
                if result and not result.startswith("[ERROR]"):
                    return result
            except Exception as exc:
                last_exc = exc
                print(f"  [LLM] {pname} falló ({exc}), probando siguiente...")
                continue

        # Final fallback: Ollama local (even if it's already in the chain, try once more)
        try:
            return self.ollama.generate(prompt, temp=temp)
        except Exception:
            raise last_exc or RuntimeError("Todos los providers fallaron")

    def _call_provider(self, provider: str, key: str, prompt: str, temp: float) -> str:
        """Instantiate and call a provider by name."""
        if provider == "claude":
            from core.llm.providers.claude_provider import ClaudeProvider
            return ClaudeProvider(api_key=key).generate(prompt, temp=temp)
        if provider == "openai":
            from core.llm.providers.openai_provider import OpenAIProvider
            return OpenAIProvider(api_key=key).generate(prompt, temp=temp)
        if provider == "deepseek":
            from core.llm.providers.deepseek_provider import DeepSeekProvider
            return DeepSeekProvider(api_key=key).generate(prompt, temp=temp)
        if provider == "groq":
            from core.llm.providers.groq_provider import GroqProvider
            return GroqProvider(api_key=key).generate(prompt, temp=temp)
        if provider == "mistral":
            from core.llm.providers.mistral_provider import MistralProvider
            return MistralProvider(api_key=key).generate(prompt, temp=temp)
        if provider == "openrouter":
            from core.llm.providers.openrouter_provider import OpenRouterProvider
            return OpenRouterProvider(api_key=key).generate(prompt, temp=temp)
        # ollama or unknown
        return self.ollama.generate(prompt, temp=temp)

    def _call(self, provider: str, prompt: str, temp: float) -> str:
        if provider == "ollama":
            return self.ollama.generate(prompt, temp=temp)
        else:
            return self.mock.generate(prompt)


# Singleton (global access)
router = LLMRouter()

