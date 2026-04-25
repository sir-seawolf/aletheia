"""El analista frío. Busca en memoria, selecciona lo relevante, detecta falta de datos."""

import json
from typing import Dict, Any, List
from core.context import Context
from ai.ollama_client import generate
from ai.prompts import exploration_prompt


def run(context: Context) -> Dict[str, Any]:
    """
    Explora la memoria y el contexto para extraer hechos relevantes.

    Args:
        context: Contexto completo de la solicitud

    Returns:
        Estructura con facts, gaps y confidence
    """
    # Intentar extracción con IA; fallback a lógica estructurada
    ai_result = _try_extract_with_ai(context)
    if ai_result:
        return ai_result

    # Fallback: análisis simple basado en palabras clave
    memory = context.memory
    question = context.question
    domain = context.domain
    profile = context.user_profile

    facts = _extract_relevant_facts(memory, domain, question, profile)
    gaps = _detect_gaps(facts, context.risk, profile)
    confidence = _calculate_confidence(facts, gaps, profile)

    return {
        "facts": facts,
        "gaps": gaps,
        "confidence": confidence,
    }


def _try_extract_with_ai(context: Context) -> Dict[str, Any] | None:
    """Intenta extraer hechos usando Ollama. Devuelve None si falla."""
    try:
        prompt = exploration_prompt(context.to_dict())
        response = generate(prompt, temperature=0.3)

        if response.startswith("[ERROR]"):
            return None

        # Limpiar posible markdown
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        data = json.loads(cleaned)

        return {
            "facts": data.get("facts", []),
            "gaps": data.get("gaps", []),
            "confidence": data.get("confidence", 0.5),
        }
    except Exception:
        return None


def _extract_relevant_facts(
    memory: List[str],
    domain: str,
    question: str,
    profile,
) -> List[str]:
    """Extrae hechos relevantes de la memoria (fallback por keywords)."""
    keywords = set(question.lower().split())
    keywords.add(domain.lower())

    relevant = []
    for item in memory:
        item_lower = item.lower()
        if any(kw in item_lower for kw in keywords):
            relevant.append(item)

    # Ajuste por perfil
    max_items = 5
    if profile and getattr(profile, "verbosity_preference", None) == "alta":
        max_items = 10

    # Estilo cognitivo
    if profile and getattr(profile, "cognitive_style", None) == "arborescente":
        # diversidad (MVP: mantener orden original)
        return relevant[:max_items]
    else:
        # linealidad → orden temporal aproximado (por ahora orden natural)
        return relevant[:max_items]


def _detect_gaps(
    facts: List[str],
    risk_config: Dict[str, Any],
    profile,
) -> List[str]:
    """Detecta información faltante basada en el nivel de riesgo."""
    gaps = []
    min_evidence = risk_config.get("min_evidence", 0)

    if len(facts) < min_evidence:
        gaps.append(f"Se requieren al menos {min_evidence} datos relevantes. Encontrados: {len(facts)}")

    # Gap cognitivo (MUY diferencial)
    if profile and getattr(profile, "abstraction_tolerance", None) == "alta":
        if len(facts) < 3:
            gaps.append("Falta profundidad estructural para análisis complejo")

    # Gaps específicos por dominio (MVP básico)
    if risk_config.get("level") == "high":
        if not any("fecha" in f.lower() or "mes" in f.lower() or "año" in f.lower() for f in facts):
            gaps.append("Falta información temporal para análisis de alto riesgo")

    return gaps


def _calculate_confidence(
    facts: List[str],
    gaps: List[str],
    profile,
) -> float:
    """Calcula nivel de confianza en la exploración."""
    base = 0.7
    fact_boost = min(len(facts) * 0.1, 0.2)
    gap_penalty = min(len(gaps) * 0.15, 0.3)

    confidence = base + fact_boost - gap_penalty

    # ajuste cognitivo
    if profile and getattr(profile, "cognitive_style", None) == "arborescente":
        confidence += 0.05  # tolera incertidumbre

    return round(max(0.0, min(1.0, confidence)), 2)

