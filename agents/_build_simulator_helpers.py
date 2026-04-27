from typing import Dict, Any
from core.models import DecisionReport
from datetime import datetime, timezone

def _build_decision_report_from_ai(context, exploration, ai_result, session_id):
    facts = exploration.get("facts", [])
    gaps = exploration.get("gaps", [])
    
    return DecisionReport(
        interaction_id=session_id + "_simulator",
        timestamp=datetime.now(timezone.utc).isoformat(),
        domain=context.domain,
        question=context.question,
        snapshot={
            "risk": context.risk.get("level"),
            "facts_count": len(facts),
            "gaps_count": len(gaps),
            "has_temporal_data": any("fecha" in f.lower() or "mes" in f.lower() for f in facts)
        },
        facts=facts,
        gaps=gaps,
        exploration_confidence=exploration.get("confidence", 0.6),
        scenarios=ai_result.get("scenarios", []),
        risks=ai_result.get("risks", []),
        assumptions=ai_result.get("assumptions", []),
        llm_insight=ai_result.get("insight", ""),
        validation_issues=[],
        valid=True,
        overall_confidence=_calculate_overall_confidence(exploration, ai_result),
        risk_level=context.risk.get("level", "medium"),
        steps_executed=["explorer", "simulator"]
    ).to_dict()

def _calculate_overall_confidence(exploration, ai_result):
    base = exploration.get("confidence", 0.6)
    scenario_count = len(ai_result.get("scenarios", []))
    scenario_bonus = min(scenario_count * 0.05, 0.15)
    risk_penalty = 0.1 if scenario_count < 2 else 0
    return round(max(0.0, min(1.0, base + scenario_bonus - risk_penalty)), 2)
