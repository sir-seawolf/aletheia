from typing import List, Dict, Any
from memory.service import find_similar_decisions
from .regulation_engine import compute_regulation_signal, regulate_memory_weight


def build_memory_influence(
    question: str,
    domain: str,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Convierte memoria en sesgo estructural para el sistema (MRE enhanced).
    """
    similar_nodes = find_similar_decisions(question, domain, limit=limit)

    if not similar_nodes:
        return {
            "bias_summary": "no_memory",
            "influential_cases": [],
            "regulation": {
                "mode": "balanced",
                "bias_multiplier": 1.0,
                "message": "No memory available"
            }
        }

    # MRE regulation
    regulation = compute_regulation_signal(similar_nodes)
    
    # Weighted cases
    compressed = []
    for n in similar_nodes:
        similarity = n.get("similarity_score", 0.5)  # from service
        weight = regulate_memory_weight(n, similarity)
        n["weight"] = weight
        compressed.append(_compress_nodes([n])[0])  # single

    bias_summary = _build_bias_summary(similar_nodes)

    return {
        "bias_summary": bias_summary,
        "influential_cases": compressed,
        "regulation": regulation
    }


def _compress_nodes(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "question": n["question"][:100] + '...' if len(n["question"]) > 100 else n["question"],
            "expected": n.get("expected_outcome", "N/A"),
            "real": n.get("real_outcome", "N/A"),
            "error": n.get("prediction_error", 0),
            "confidence": n.get("confidence_before", 0.5),
        }
        for n in nodes
    ]


def _build_bias_summary(nodes: List[Dict[str, Any]]) -> str:
    high_error_cases = [n for n in nodes if n.get("prediction_error", 0) > 0.3]

    if len(high_error_cases) > 1:
        return (
            "Patrón histórico: errores altos en predicciones optimistas. "
            "Priorizar escenarios conservadores y reducir confianza en optimismo."
        )

    if len(nodes) > 3:
        return (
            "Historial extenso sin errores graves. Mantener distribución equilibrada "
            "pero incorporar lecciones específicas de casos similares."
        )

    return (
        "Memoria limitada. Usar casos disponibles como referencia ligera "
        "sin sesgo fuerte."
    )
