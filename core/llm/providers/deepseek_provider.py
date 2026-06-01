"""
DeepSeek provider — OpenAI-compatible API.

Free tier available at platform.deepseek.com
API key: PALACE/config/preferences.json  →  llm.providers list
         or env var DEEPSEEK_API_KEY

Default model: deepseek-chat (DeepSeek-V3, context 64k)
"""

from typing import Optional


class DeepSeekProvider:

    BASE_URL = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-chat"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODEL

    def _client(self):
        import openai, os
        key = self.api_key or os.getenv("DEEPSEEK_API_KEY", "")
        if not key:
            raise RuntimeError(
                "API key de DeepSeek no configurada. "
                "Añádela en Configuración > LLM o en DEEPSEEK_API_KEY."
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
        return bool(self.api_key or os.getenv("DEEPSEEK_API_KEY", ""))
