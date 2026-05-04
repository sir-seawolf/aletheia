"""
Explorer Agent - Cold analyst: memory search, relevance selection, gap detection.

STATUS: IMPLEMENTED (production v1.1)
Dependencies: core.context, core.llm.router, memory.models, core.event_bus
Last stable version: v1.1

Responsibility: Extract facts/gaps from memory/context for simulator input.
Fallback to keyword if LLM fails.
"""

import json
import re
from typing import Dict, Any, List, Optional, Sequence, Union
from core.context import Context
from core.event_bus import build_event, emit_event
from core.llm import router, exploration_prompt
from memory.models import MemoryNode

def run(domain: str, question: str, policy: Optional[Dict[str, Any]] = None, session_id: str = "local", memory=None, user_profile_str: str = "") -> Dict[str, Any]:
    """
    Main explorer interface for orchestrator.

    Args:
        domain (str): Problem domain
        question (str): Decision question
        policy (dict, optional): ACO policy dict
        session_id (str): Event bus session
        user_profile_str (str): Pre-formatted profile context for LLM injection

    Returns:
        dict: {'facts': list, 'gaps': list, 'confidence': float, 'llm_calls': int}
    """
    context = Context(
        domain=domain,
        question=question,
        memory=memory or [],
        risk={},
        user_profile=None,
        user_profile_str=user_profile_str,
    )

    if policy:
        context.constraints.append(f"aco_policy:{policy.get('mode', 'unknown')}")

    return _run(context, session_id)

def _run(context, session_id: str = "local") -> Dict[str, Any]:
    domain = getattr(context, "domain", "unknown")
    question = getattr(context, "question", "unknown")
    """
    Explora la memoria y el contexto para extraer hechos relevantes.

    Args:
        context: Contexto completo de la solicitud

    Returns:
        Estructura con facts, gaps y confidence
    """
    emit_event(
        build_event(
            session_id=session_id,
            agent="explorer",
            stage="thinking",
            event_type="searching_memory",
            payload={"domain": domain},
            confidence=0.0,
        )
    )

    # Similar decisions from memory for facts enhancement (Sprint 2)
    similar_decisions = context.memory_service.find_similar_decisions(
        context.question, 
        context.domain, 
        limit=3
    ) if hasattr(context, 'memory_service') else []

    enhanced_memory = context.memory + [f"Similar past decision: {d.get('question', '')} -> outcome: {d.get('expected_outcome', 'N/A')}" for d in similar_decisions]

    # Intentar extracción con IA; fallback a lógica estructurada
    ai_result = _try_extract_with_ai(context)
    if ai_result:
        emit_event(
            build_event(
                session_id=session_id,
                agent="explorer",
                stage="done",
                event_type="facts_extracted",
                payload={
                    "facts": ai_result.get("facts", []),
                    "gaps": ai_result.get("gaps", []),
                    "similar_used": len(similar_decisions),
                },
                confidence=float(ai_result.get("confidence", 0.0)),
            )
        )
        return ai_result

    # Fallback: análisis simple basado en palabras clave with enhanced memory
    memory = enhanced_memory
    question = context.question
    domain = context.domain
    profile = context.user_profile

    facts = _extract_relevant_facts(memory, domain, question, profile)
    gaps = _detect_gaps(facts, context.risk, profile)
    confidence = _calculate_confidence(facts, gaps, profile)

    result = {
        "domain": domain,
        "question": context.question,
        "facts": facts,
        "gaps": gaps,
        "confidence": confidence,
        "similar_used": len(similar_decisions),
        "llm_calls": 1 if ai_result else 0  # ACO metric
    }

    emit_event(
        build_event(
            session_id=session_id,
            agent="explorer",
            stage="done",
            event_type="facts_extracted",
            payload={"facts": facts, "gaps": gaps},
            confidence=confidence,
        )
    )

    return result


def _try_extract_with_ai(context: Context) -> Optional[Dict[str, Any]]:
    """
    Intenta extraer hechos usando LLMRouter.
    Tries strict JSON parse first, then regex extraction, then free-text fallback.
    Returns None only if the LLM call itself fails.
    """
    try:
        prompt = exploration_prompt(context.to_dict())
        response = router.generate(task="exploration", prompt=prompt, context={"domain": context.domain}, temp=0.3)

        if not response or response.startswith("[ERROR]") or response.startswith("[MOCK]"):
            return None

        # Strip markdown fences
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = [l for l in cleaned.splitlines() if not l.startswith("```")]
            cleaned = "\n".join(lines).strip()

        # 1. Direct JSON parse
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return {
                    "domain": context.domain,
                    "question": context.question,
                    "facts": data.get("facts", []),
                    "gaps": data.get("gaps", []),
                    "confidence": float(data.get("confidence", 0.6)),
                }
        except ValueError:
            pass

        # 2. Regex: find first {...} block containing "facts"
        m = re.search(r'\{[^{}]*"facts"[^{}]*\}', cleaned, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group())
                return {
                    "domain": context.domain,
                    "question": context.question,
                    "facts": data.get("facts", []),
                    "gaps": data.get("gaps", []),
                    "confidence": float(data.get("confidence", 0.5)),
                }
            except ValueError:
                pass

        # 3. Free-text fallback: use non-empty lines as facts
        lines = [
            l.strip().lstrip("•-*▸1234567890.)").strip()
            for l in cleaned.split("\n")
            if l.strip() and len(l.strip()) > 15
        ]
        return {
            "domain": context.domain,
            "question": context.question,
            "facts": lines[:5] if lines else [f"Análisis: {context.question}"],
            "gaps": ["Formato de respuesta no estructurado"],
            "confidence": 0.4,
        }
    except Exception:
        return None


def _extract_relevant_facts(
    memory: Sequence[Union[MemoryNode, str]],
    domain: str,
    question: str,
    profile,
) -> List[str]:
    """Extrae hechos relevantes de la memoria (fallback por keywords), soportando MemoryNode y str."""
    keywords = set(question.lower().split())
    keywords.add(domain.lower())

    relevant: List[str] = []
    for item in memory:
        if isinstance(item, MemoryNode):
            node_domain = (item.meta.domain or "").lower()
            text = f"{item.title} {item.content}".lower()
            if node_domain and node_domain != domain.lower():
                continue
            if any(kw in text for kw in keywords):
                relevant.append(f"{item.title}: {item.content}")
        else:
            item_lower = str(item).lower()
            if any(kw in item_lower for kw in keywords):
                relevant.append(str(item))

    # Ajuste por perfil
    max_items = 5
    if profile and getattr(profile, "verbosity_preference", None) == "alta":
        max_items = 10

    # Estilo cognitivo
    if profile and getattr(profile, "cognitive_style", None) == "arborescente":
        return relevant[:max_items]
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

# enrich_with_ollama deprecated - use orchestrator.router.enrich("exploration")
pass

