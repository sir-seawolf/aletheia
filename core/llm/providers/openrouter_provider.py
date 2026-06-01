"""
OpenRouter provider — aggregates 20+ free and paid models via one API key.

Free-tier models (no credit card, just register at openrouter.ai):
  google/gemma-3-27b-it:free
  meta-llama/llama-3.3-70b-instruct:free
  deepseek/deepseek-chat-v3-0324:free
  mistralai/mistral-7b-instruct:free
  microsoft/phi-4-reasoning-plus:free

API is OpenAI-compatible. Key from openrouter.ai (free registration).
"""

from typing import Optional


class OpenRouterProvider:

    BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = "meta-llama/llama-3.3-70b-instruct:free"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL

    def _client(self):
        import openai, os
        key = self.api_key or os.getenv("OPENROUTER_API_KEY", "")
        if not key:
            raise RuntimeError(
                "API key de OpenRouter no configurada. "
                "Regístrate gratis en openrouter.ai y añádela en Configuración > LLM."
            )
        return openai.OpenAI(
            api_key=key,
            base_url=self.BASE_URL,
            default_headers={
                "HTTP-Referer": "https://github.com/aletheia-ai/aletheia",
                "X-Title": "Aletheia",
            },
        )

    def generate(self, prompt: str, temp: float = 0.3, model: Optional[str] = None) -> str:
        client = self._client()
        response = client.chat.completions.create(
            model=model or self.model,
            temperature=temp,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()

    def list_free_models(self) -> list[str]:
        """Return curated list of free OpenRouter models (no API call needed)."""
        return [
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemma-3-27b-it:free",
            "deepseek/deepseek-chat-v3-0324:free",
            "mistralai/mistral-7b-instruct:free",
            "microsoft/phi-4-reasoning-plus:free",
        ]

    def is_available(self) -> bool:
        import os
        return bool(self.api_key or os.getenv("OPENROUTER_API_KEY", ""))
