"""
Mistral AI provider.

Free tier at console.mistral.ai
API key: PALACE/config/preferences.json  →  llm.providers list
         or env var MISTRAL_API_KEY

Requires: pip install mistralai
Default model: mistral-small-latest
"""

from typing import Optional


class MistralProvider:

    DEFAULT_MODEL = "mistral-small-latest"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL

    def _client(self):
        import os
        try:
            from mistralai import Mistral
        except ImportError:
            raise RuntimeError("Instala mistralai: pip install mistralai")
        key = self.api_key or os.getenv("MISTRAL_API_KEY", "")
        if not key:
            raise RuntimeError(
                "API key de Mistral no configurada. "
                "Añádela en Configuración > LLM o en MISTRAL_API_KEY."
            )
        return Mistral(api_key=key)

    def generate(self, prompt: str, temp: float = 0.3, model: Optional[str] = None) -> str:
        client = self._client()
        response = client.chat.complete(
            model=model or self.model,
            temperature=temp,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()

    def is_available(self) -> bool:
        import os
        return bool(self.api_key or os.getenv("MISTRAL_API_KEY", ""))
