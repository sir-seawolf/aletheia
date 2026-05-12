import requests
from typing import Optional

class OllamaProvider:
    def __init__(self, url: str = "http://localhost:11434"):
        self.url = url
        self.default_model = "llama3.2:3b"

    def generate(self, prompt: str, temp: float = 0.3, model: Optional[str] = None) -> str:
        model = model or self.default_model
        payload = {
            "model": model,
            "prompt": str(prompt),
            "temperature": temp,
            "stream": False
        }
        try:
            r = requests.post(f"{self.url}/api/generate", json=payload, timeout=120)
            r.raise_for_status()
            return r.json().get("response", "").strip()
        except Exception as e:
            raise Exception(f"Ollama error: {str(e)}")

