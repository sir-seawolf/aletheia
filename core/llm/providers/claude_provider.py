"""
Anthropic Claude provider for LLMRouter.

Requires:  pip install anthropic
API key:   PALACE/config/preferences.json  →  {"llm": {"provider": "claude", "api_key": "sk-ant-..."}}
           or env var ANTHROPIC_API_KEY
"""

from typing import Optional


class ClaudeProvider:

    DEFAULT_MODEL = "claude-sonnet-4-6"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL

    def _client(self):
        import anthropic
        key = self.api_key or __import__("os").getenv("ANTHROPIC_API_KEY", "")
        if not key:
            raise RuntimeError(
                "API key de Claude no configurada. "
                "Añádela en Configuración > LLM o en la variable de entorno ANTHROPIC_API_KEY."
            )
        return anthropic.Anthropic(api_key=key)

    def generate(self, prompt: str, temp: float = 0.3, model: Optional[str] = None) -> str:
        client = self._client()
        response = client.messages.create(
            model=model or self.model,
            max_tokens=1024,
            temperature=temp,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    def is_available(self) -> bool:
        import os
        key = self.api_key or os.getenv("ANTHROPIC_API_KEY", "")
        return bool(key)
