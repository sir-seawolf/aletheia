"""
LLM Provider Selector v1
Decide qué cerebro usar: ollama / mock / (online futuro)
"""

import requests


def _ollama_alive() -> bool:
    try:
        r = requests.get("http://localhost:11434", timeout=1)
        return r.status_code == 200
    except:
        return False


def _estimate_complexity(prompt: str) -> float:
    """
    Heurística simple (offline):
    - longitud
    - keywords de razonamiento
    """

    p = prompt.lower()

    score = 0.0

    # longitud
    score += min(len(prompt) / 2000, 1.0)

    # razonamiento
    keywords = ["why", "compare", "analyze", "risk", "strategy", "simulate", "decide"]
    score += sum(0.1 for k in keywords if k in p)

    return min(score, 1.0)


def select_provider(task: str, prompt: str, confidence: float = 0.5) -> str:
    """
    Devuelve:
    - "ollama"
    - "mock"
    """

    ollama_ok = _ollama_alive()
    complexity = _estimate_complexity(prompt)

    # 🔥 REGLA 1: si no hay ollama → mock
    if not ollama_ok:
        return "mock"

    # 🔥 REGLA 2: tareas simples → ollama ligero
    if complexity < 0.3:
        return "ollama"

    # 🔥 REGLA 3: tareas medias
    if 0.3 <= complexity < 0.7:
        return "ollama"

    # 🔥 REGLA 4: alta complejidad → ollama sí o sí
    return "ollama"

