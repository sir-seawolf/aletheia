"""
OpenAI provider for LLMRouter.

Requires:  pip install openai
API key:   PALACE/config/preferences.json  →  {"llm": {"provider": "openai", "api_key": "sk-..."}}
           or env var OPENAI_API_KEY
"""

from typing import Optional


class OpenAIProvider:

    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL

    def _client(self):
        import openai, os
        key = self.api_key or os.getenv("OPENAI_API_KEY", "")
        if not key:
            raise RuntimeError(
                "API key de OpenAI no configurada. "
                "Añádela en Configuración > LLM o en la variable de entorno OPENAI_API_KEY."
            )
        return openai.OpenAI(api_key=key)

    def generate(self, prompt: str, temp: float = 0.3, model: Optional[str] = None) -> str:
        client = self._client()
        response = client.chat.completions.create(
            model=model or self.model,
            temperature=temp,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()

    def is_available(self) -> bool:
        import os
        key = self.api_key or os.getenv("OPENAI_API_KEY", "")
        return bool(key)
