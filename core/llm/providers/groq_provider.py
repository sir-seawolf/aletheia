"""
Groq provider — ultra-fast inference, free tier.

Free at console.groq.com (rate-limited but fast)
API key: PALACE/config/preferences.json  →  llm.providers list
         or env var GROQ_API_KEY

Default model: llama-3.3-70b-versatile (best quality on free tier)
Other options: mixtral-8x7b-32768, gemma2-9b-it
"""

from typing import Optional


class GroqProvider:

    BASE_URL = "https://api.groq.com/openai/v1"
    DEFAULT_MODEL = "llama-3.3-70b-versatile"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL

    def _client(self):
        import openai, os
        key = self.api_key or os.getenv("GROQ_API_KEY", "")
        if not key:
            raise RuntimeError(
                "API key de Groq no configurada. "
                "Añádela en Configuración > LLM o en GROQ_API_KEY."
            )
        return openai.OpenAI(api_key=key, base_url=self.BASE_URL)

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
        return bool(self.api_key or os.getenv("GROQ_API_KEY", ""))
