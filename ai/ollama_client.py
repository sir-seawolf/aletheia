"""Cliente para interactuar con Ollama (inferencia local)."""

import requests
import json
from typing import Optional
from config import MODEL, TEMPERATURE


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
        return "[ERROR] No se pudo conectar con Ollama. ¿Está ejecutándose en localhost:11434?"
    except requests.exceptions.Timeout:
        return "[ERROR] Tiempo de espera agotado al llamar a Ollama."
    except Exception as e:
        return f"[ERROR] {str(e)}"

