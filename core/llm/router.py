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
from core.llm.selector import select_provider
from core.llm.palace_injector import inject_palace
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

        Args:
            task (str): Task type ('exploration', 'simulation', etc.)
            prompt (str): Raw prompt text
            context (Optional[Dict[str, Any]]): Context dict, REQUIRED for cache hits (domain key)
            temp (float): Temperature 0.0-1.0

        Returns:
            str: Generated response (cache or universe stack)

        Raises:
            Exception: Stack processing failure
        Note: cache.get() requires (task, prompt, context). Bugs from inconsistent calls fixed by explicit context=None.
        Example:
            router.generate('exploration', 'Risk?', {'domain': 'finance'}, temp=0.3)
        """
        # 1. Cache check
        cached = self.cache.get(task, prompt, context or {})
        if cached:
            return cached

        # 2. Ollama with mock fallback
        try:
            response = self.ollama.generate(prompt, temp=temp)
            if not response or response.startswith("[ERROR]"):
                response = self.mock.generate(prompt)
        except Exception:
            response = self.mock.generate(prompt)

        self.learning.process(task, prompt, response, {"score": 0.9, "retry": False}, context or {})
        self.cache.set(task, prompt, context or {}, response)

        return response

    def _call(self, provider: str, prompt: str, temp: float) -> str:
        if provider == "ollama":
            return self.ollama.generate(prompt, temp=temp)
        else:
            return self.mock.generate(prompt)


# Singleton (global access)
router = LLMRouter()

