"""El analista frío. Busca en memoria, selecciona lo relevante, detecta falta de datos."""

from typing import Dict, Any, List
from core.context import Context


def run(context: Context) -> Dict[str, Any]:
    """
    Explora la memoria y el contexto para extraer hechos relevantes.

    Args:
        context: Contexto completo de la solicitud

    Returns:
        Estructura con facts, gaps y confidence
    """
    memory = context.memory
    question = context.question
    domain = context.domain

    # MVP: análisis simple basado en palabras clave del dominio
    # En el futuro esto usará retrieval con embeddings
    facts = _extract_relevant_facts(memory, domain, question)
    gaps = _detect_gaps(facts, context.risk)

    confidence = _calculate_confidence(facts, gaps)

    return {
        "facts": facts,
        "gaps": gaps,
        "confidence": confidence,
    }


def _extract_relevant_facts(memory: List[str], domain: str, question: str) -> List[str]:
    """Extrae hechos relevantes de la memoria."""
    # MVP: filtro simple por palabras clave
    keywords = set(question.lower().split())
    keywords.add(domain.lower())

    relevant = []
    for item in memory:
        item_lower = item.lower()
        if any(kw in item_lower for kw in keywords):
            relevant.append(item)

    return relevant


def _detect_gaps(facts: List[str], risk_config: Dict[str, Any]) -> List[str]:
    """Detecta información faltante basada en el nivel de riesgo."""
    gaps = []
    min_evidence = risk_config.get("min_evidence", 0)

    if len(facts) < min_evidence:
        gaps.append(f"Se requieren al menos {min_evidence} datos relevantes. Encontrados: {len(facts)}")

    # Gaps específicos por dominio (MVP básico)
    if risk_config.get("level") == "high":
        if not any("fecha" in f.lower() or "mes" in f.lower() or "año" in f.lower() for f in facts):
            gaps.append("Falta información temporal para análisis de alto riesgo")

    return gaps


def _calculate_confidence(facts: List[str], gaps: List[str]) -> float:
    """Calcula nivel de confianza en la exploración."""
    base = 0.7
    fact_boost = min(len(facts) * 0.1, 0.2)
    gap_penalty = min(len(gaps) * 0.15, 0.3)
    return round(max(0.0, min(1.0, base + fact_boost - gap_penalty)), 2)

