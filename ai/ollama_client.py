"""
Legacy Ollama client (DEPRECATED).

STATUS: PLACEHOLDER (legacy v1 client)
Dependencies: requests
Last stable version: v1.0

Direct Ollama API calls. Migrate to core.llm.router.generate().

Functions:
- generate(prompt: str, temp: float=0.7, model: Optional[str]=None) → str
  Target: llama3 local (localhost:11434)
  Length: variable, timeout 120s
- healthcheck() → dict

TODO: MIGRATE all calls to router.generate(task, prompt, context)
"""

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
    Legacy direct Ollama generate (DEPRECATED: use router.generate()).

    Args:
        prompt (str): Input prompt
        temperature (float): 0.0 determinist, 1.0 creative
        model (Optional[str]): e.g. 'llama3', default MODEL

    Returns:
        str: Generated text or error string

    Target model: llama3 on localhost:11434, ~timeout 120s
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

