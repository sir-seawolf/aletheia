"""
Explorer — cold analyst for the v1 cognitive pipeline.

Responsibility: extract facts/gaps from memory/context for simulator input.
Fallback to keyword analysis if LLM fails.
"""

import json
import re
from typing import Dict, Any, List, Optional, Sequence, Union

from core.context import Context
from core.event_bus import build_event, emit_event
from core.llm import router, exploration_prompt
from memory.models import MemoryNode


def run(
    domain: str,
    question: str,
    policy: Optional[Dict[str, Any]] = None,
    session_id: str = "local",
    memory=None,
    user_profile_str: str = "",
) -> Dict[str, Any]:
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


def _run(context: Context, session_id: str = "local") -> Dict[str, Any]:
    domain   = getattr(context, "domain", "unknown")
    question = getattr(context, "question", "unknown")

    emit_event(build_event(
        session_id=session_id, agent="explorer", stage="thinking",
        event_type="searching_memory", payload={"domain": domain}, confidence=0.0,
    ))

    similar_decisions = (
        context.memory_service.find_similar_decisions(context.question, context.domain, limit=3)
        if hasattr(context, "memory_service") else []
    )
    enhanced_memory = context.memory + [
        f"Similar past decision: {d.get('question', '')} -> outcome: {d.get('expected_outcome', 'N/A')}"
        for d in similar_decisions
    ]

    ai_result = _try_extract_with_ai(context)
    if ai_result:
        emit_event(build_event(
            session_id=session_id, agent="explorer", stage="done",
            event_type="facts_extracted",
            payload={"facts": ai_result.get("facts", []), "gaps": ai_result.get("gaps", []),
                     "similar_used": len(similar_decisions)},
            confidence=float(ai_result.get("confidence", 0.0)),
        ))
        return ai_result

    profile = context.user_profile
    facts   = _extract_relevant_facts(enhanced_memory, domain, question, profile)
    gaps    = _detect_gaps(facts, context.risk, profile)
    conf    = _calculate_confidence(facts, gaps, profile)

    result = {
        "domain":       domain,
        "question":     question,
        "facts":        facts,
        "gaps":         gaps,
        "confidence":   conf,
        "similar_used": len(similar_decisions),
        "llm_calls":    0,
    }
    emit_event(build_event(
        session_id=session_id, agent="explorer", stage="done",
        event_type="facts_extracted",
        payload={"facts": facts, "gaps": gaps}, confidence=conf,
    ))
    return result


def _try_extract_with_ai(context: Context) -> Optional[Dict[str, Any]]:
    try:
        prompt   = exploration_prompt(context.to_dict())
        response = router.generate(task="exploration", prompt=prompt,
                                   context={"domain": context.domain}, temp=0.3)
        if not response or response.startswith("[ERROR]") or response.startswith("[MOCK]"):
            return None

        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = "\n".join(l for l in cleaned.splitlines() if not l.startswith("```")).strip()

        try:
            data = json.loads(cleaned)
            if isinstance(data, dict):
                return {
                    "domain": context.domain, "question": context.question,
                    "facts": data.get("facts", []), "gaps": data.get("gaps", []),
                    "confidence": float(data.get("confidence", 0.6)),
                }
        except ValueError:
            pass

        m = re.search(r'\{[^{}]*"facts"[^{}]*\}', cleaned, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group())
                return {
                    "domain": context.domain, "question": context.question,
                    "facts": data.get("facts", []), "gaps": data.get("gaps", []),
                    "confidence": float(data.get("confidence", 0.5)),
                }
            except ValueError:
                pass

        lines = [
            l.strip().lstrip("•-*▸1234567890.)").strip()
            for l in cleaned.split("\n")
            if l.strip() and len(l.strip()) > 15
        ]
        return {
            "domain": context.domain, "question": context.question,
            "facts": lines[:5] if lines else [f"Análisis: {context.question}"],
            "gaps": ["Respuesta LLM sin estructura JSON — análisis basado en texto libre"],
            "confidence": 0.55,
        }
    except Exception:
        return None


def _extract_relevant_facts(
    memory: Sequence[Union[MemoryNode, str]],
    domain: str,
    question: str,
    profile,
) -> List[str]:
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
            if any(kw in str(item).lower() for kw in keywords):
                relevant.append(str(item))

    max_items = 10 if (profile and getattr(profile, "verbosity_preference", None) == "alta") else 5
    return relevant[:max_items]


def _detect_gaps(facts: List[str], risk_config: Dict[str, Any], profile) -> List[str]:
    gaps = []
    min_ev = risk_config.get("min_evidence", 0)
    if len(facts) < min_ev:
        gaps.append(f"Se requieren al menos {min_ev} datos relevantes. Encontrados: {len(facts)}")
    if profile and getattr(profile, "abstraction_tolerance", None) == "alta" and len(facts) < 3:
        gaps.append("Falta profundidad estructural para análisis complejo")
    if risk_config.get("level") == "high":
        if not any("fecha" in f.lower() or "mes" in f.lower() or "año" in f.lower() for f in facts):
            gaps.append("Falta información temporal para análisis de alto riesgo")
    return gaps


def _calculate_confidence(facts: List[str], gaps: List[str], profile) -> float:
    base       = 0.7
    fact_boost = min(len(facts) * 0.1, 0.2)
    gap_pen    = min(len(gaps) * 0.15, 0.3)
    conf       = base + fact_boost - gap_pen
    if profile and getattr(profile, "cognitive_style", None) == "arborescente":
        conf += 0.05
    return round(max(0.0, min(1.0, conf)), 2)
