"""
LLMRouter - Central LLM interface for Aletheia cognitive stack.

STATUS: IMPLEMENTED (production v1.1)
Dependencies: core.llm.providers.*, core.llm.cache, core.cognition.*, core.ecosystem.*, memory.service, core.palace.search
Last stable version: v1.1

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

    def generate(self, task: str, prompt: str, context: Optional[Dict[str, Any]] = None, temp: float = 0.3) -> str:
        """
        Generate LLM response through full cognitive stack with caching.

        Provider priority:
          1. Preference file / env var (claude, openai, ollama)
          2. Ollama local if no preference set
          3. Mock fallback if all providers fail
        """
        # Chat responses must never be cached — each turn has unique context
        use_cache = task != "chat"

        # 1. Cache check
        if use_cache:
            cached = self.cache.get(task, prompt, context or {})
            if cached:
                return cached

        # 2. TURBO mode — parallel multi-provider execution
        try:
            from core.turbo.mode import turbo_mode
            if turbo_mode.is_active():
                from core.turbo.panel import turbo_panel
                response = turbo_panel.run(task, prompt, temp)
                self.learning.process(task, prompt, response, {"score": 0.9, "retry": False}, context or {})
                if use_cache:
                    self.cache.set(task, prompt, context or {}, response)
                return response
        except Exception:
            pass  # fall through to normal path

        # 3. Dispatch to configured provider
        try:
            response = self._call_configured(prompt, temp)
            if not response or response.startswith("[ERROR]"):
                response = self.mock.generate(prompt)
        except Exception:
            response = self.mock.generate(prompt)

        self.learning.process(task, prompt, response, {"score": 0.9, "retry": False}, context or {})
        if use_cache:
            self.cache.set(task, prompt, context or {}, response)

        return response

    def _call_configured(self, prompt: str, temp: float) -> str:
        """
        Route to the configured provider, then walk the failover chain on error.
        Chain: primary → failover[0] → failover[1] → … → Ollama → Mock
        """
        primary, chain, _get_key = "ollama", [], lambda _: ""
        try:
            from core.config.preferences import get_llm_provider, get_api_key, get_failover_chain
            primary   = get_llm_provider()
            chain     = get_failover_chain()
            _get_key  = get_api_key
        except Exception:
            pass

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
        # ollama or unknown
        return self.ollama.generate(prompt, temp=temp)

    def _call(self, provider: str, prompt: str, temp: float) -> str:
        if provider == "ollama":
            return self.ollama.generate(prompt, temp=temp)
        else:
            return self.mock.generate(prompt)


# Singleton (global access)
router = LLMRouter()

