"""
LLMRouter v3 - Full Ruta Aletheia Cognitive Universe
Legacy V2 + Prefrontal + SelfAware + ACL + Economy + SOI + Genome + Ecosystem + Civilization + Universe.
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

        # 1. Legacy Cache Check
        cached = self.cache.get(task, prompt, context or {})
        if cached:
            return cached

        input_data = {
            "task": task,
            "prompt": prompt,
            "question": prompt,
            "raw_input": prompt,
            "context": context or {},
            "temp": temp,
            "domain": context.get("domain", "global") if context else "global"
        }

        # Full Cognitive Universe Process
        universe_result = self.universe.process(input_data)

        # Extract response str from nested (Universe → Civ → Eco → ...)
        response = universe_result.get("output")
        if isinstance(response, dict):
            response = response.get("final_output", {}).get("content", response.get("answer", str(response)))
        response = str(response) if response else "Cognitive universe processed: internal resolution."

        # Preserve legacy integration
        evaluation = {"score": 0.9, "retry": False, "stack_used": "universe"}
        self.learning.process(task, prompt, response, evaluation, context)
        self.cache.set(task, prompt, context or {}, response)

        return response

    def _call(self, provider: str, prompt: str, temp: float) -> str:
        if provider == "ollama":
            return self.ollama.generate(prompt, temp=temp)
        else:
            return self.mock.generate(prompt)


# Singleton (global access)
router = LLMRouter()

