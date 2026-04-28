from ai.ollama_client import generate as ollama_generate
from typing import Optional, Dict, Any
import requests

class LLMRouter:
    def __init__(self, mode: str = "auto"):
        self.mode = mode  # auto | offline | online | mock

    def _ollama_available(self) -> bool:
        \"\"\"
        Ping Ollama health.
        \"\"\"
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            return response.status_code == 200
        except:
            return False

    def choose_backend(self, context=None):
        # PRIORIDAD FIJA
        if self.mode == "offline":
            return "ollama"
        if self.mode == "online":
            return "online"  # futuro
        return "ollama" if self._ollama_available() else "mock"

    def enrich(self, stage: str, input: Dict[str, Any], context=None):
        backend = self.choose_backend(context)

        if backend == "ollama":
            prompt = self._build_prompt(stage, input, context)
            result = ollama_generate(prompt)
            input["llm_enrichment"] = result
            return input

        if backend == "mock":
            input["llm_enrichment"] = f"[MOCK {stage.upper()}] Deterministic fallback."
            return input

        return input

    def _build_prompt(self, stage: str, input: Dict[str, Any], context=None):
        return f"""
STAGE: {stage}
DOMAIN: {input.get('domain', 'unknown')}
QUESTION: {input.get('question', 'unknown')}
INPUT DATA: {input}

Provide structured enrichment for {stage} stage.
"""

