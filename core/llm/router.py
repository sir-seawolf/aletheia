"""
LLMRouter v2+ - Cognitive Stack Completo
Cache V2 contextual + Palace injection + Evaluator self-reflection + Learning Loop + Palace Search Engine.
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


class LLMRouter:

    def __init__(self):
        self.ollama = OllamaProvider()
        self.mock = MockProvider()
        self.cache = LLMCacheV2()
        self.evaluator = ResponseEvaluator()
        self.learning = LearningLoop()
        self.palace_search = PalaceSearchEngine()

    def generate(self, task: str, prompt: str, context: Optional[Dict[str, Any]] = None, temp: float = 0.3) -> str:

        # 1. CACHE V2 CHECK
        cached = self.cache.get(task, prompt, context or {})
        if cached:
            return cached

        domain = context.get("domain", "global") if context else "global"

        # 2. COGNITIVE CONTEXT RETRIEVAL (PCSE + Memory)
        palace_hits = self.palace_search.search(domain, prompt)
        memory_hits = retrieve_context(domain)

        # 3. PALACE INJECTION ENRICHMENT
        enriched_prompt = inject_palace(prompt, domain, task)

        # 4. PROVIDER SELECTION INTELIGENTE
        provider = select_provider(task, enriched_prompt, context.get("confidence", 0.5) if context else 0.5)

        # 5. GENERACIÓN INICIAL
        response = self._call(provider, enriched_prompt, temp)

        # 6. SELF-EVALUATION & RETRY
        evaluation = self.evaluator.evaluate(enriched_prompt, response, context)

        if evaluation["retry"]:
            fallback_prompt = enriched_prompt + "\n\nImprove clarity, completeness and relevance."
            response = self._call(provider, fallback_prompt, temp)
            evaluation = self.evaluator.evaluate(fallback_prompt, response, context)

        # 7. LEARNING LOOP (Memory + Palace update)
        self.learning.process(task, prompt, response, evaluation, context)

        # 8. CACHE V2 STORE
        self.cache.set(task, prompt, context or {}, response)

        return response

    def _call(self, provider: str, prompt: str, temp: float) -> str:
        if provider == "ollama":
            return self.ollama.generate(prompt, temp=temp)
        else:
            return self.mock.generate(prompt)


# Singleton
router = LLMRouter()

