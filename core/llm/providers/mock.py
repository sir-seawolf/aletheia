from typing import Optional

class MockProvider:
    def __init__(self):
        pass

    def generate(self, prompt: str, temp: float = 0.3, model: Optional[str] = None) -> str:
        # Deterministic fallback
        return f"[MOCK LLM] Processed prompt: {prompt[:100]}... (temp={temp}). Fallback response for {model or 'default'}."

