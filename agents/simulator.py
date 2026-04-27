"""Simulator - Genera escenarios puros sin validacion."""

from typing import Dict, Any, List

def run(exploration: Dict[str, Any]) -> Dict[str, Any]:
    """
    Genera escenarios, riesgos, supuestos desde exploration.
    No valida/normaliza.
    """
    # Mock for FASE 1 - replace with real LLM generation
    domain = exploration.get("domain", "unknown") if "domain" in exploration else "test"
    question = exploration.get("question", "unknown") if "question" in exploration else "test question"
    
    return {
        "scenarios": [
            {
                "id": "s1",
                "description": f"Escenario optimista para {domain}: {question}",
                "outcome": "positivo",
                "probability": 0.6
            },
            {
                "id": "s2",
                "description": f"Escenario conservador para {domain}: {question}",
                "outcome": "neutral",
                "probability": 0.4
            }
        ],
        "risks": {"volatilidad": 0.3, "incertidumbre": 0.5},
        "assumptions": ["Mercado estable", "Datos precisos"],
        "llm_insight": {
            "insight": "Analisis muestra balance entre optimismo y riesgo. Recomendacion conservadora.",
            "recommendation_bias": "conservative"
        },
        "exploration_confidence": exploration.get("confidence", 0.5)
    }

