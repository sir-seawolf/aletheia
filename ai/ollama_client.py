# DEPRECATED: Use core/llm/providers/ollama.py
# Legacy Ollama client - migrate all imports to new LLMRouter
"""
Legacy Ollama client. Migrate to LLMRouter.
"""
pass  # Keep for compatibility, but all new code uses router

import requests
import json
from typing import Optional
MODEL = "llama3"
TEMPERATURE = 0.7


def healthcheck() -> dict:
    """
    Healthcheck for Ollama.
    """
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        response.raise_for_status()
        models = response.json().get("models", [])
        return {"status": "healthy", "models_available": len(models), "models": [m["name"] for m in models[:3]]}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def generate(prompt: str, temperature: float = TEMPERATURE, model: Optional[str] = None) -> str:
    """
    Genera texto usando Ollama local.

    Args:
        prompt: Texto de entrada para el modelo
        temperature: Control de creatividad (0.0 = determinista, 1.0 = creativo)
        model: Modelo a usar (por defecto el configurado en config.py)

    Returns:
        Texto generado por el modelo
    """
    model_name = model or MODEL

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                },
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()

    except requests.exceptions.ConnectionError:
        return "[ERROR] No se pudo conectar con Ollama. ¿Está ejecutándose en localhost:11434? Run: ollama serve"
    except requests.exceptions.Timeout:
        return "[ERROR] Tiempo de espera agotado al llamar a Ollama."
    except Exception as e:
        return f"[ERROR] {str(e)}"

