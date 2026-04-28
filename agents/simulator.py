"""Simulator - DecisionReport Generator with Router (LLMRouter integrated)"""

from typing import Dict, Any, List
from core.schemas.decision_contract import DecisionReport
from core.llm import router
from datetime import datetime

def run(exploration: Dict[str, Any], policy: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Genera escenarios, riesgos, supuestos desde exploration.
    LLM via router.generate with policy temp.
    """
    domain = exploration.get("domain", "unknown")
    question = exploration.get("question", "unknown")
    facts = exploration.get("facts", [])
    gaps = exploration.get("gaps", [])

    temp = policy.get("temperature", 0.3) if policy else 0.3

    # LLM via orchestrator.router.enrich("simulation", simulation)
    explain_prompt = f"Provide detailed explanation for {domain} {question}. Facts: {facts}. Gaps: {gaps}."
    llm_explanation = router.generate(task="simulator", prompt=explain_prompt, context={"domain": domain}, temp=temp)
    llm_calls = 1

    insight_prompt = f"Summarize insight for {domain}: {question}. Bias?"
    llm_insight = router.generate(task="simulator", prompt=insight_prompt, context={"domain": domain}, temp=temp)
    llm_calls += 1

    data = DecisionReport(
        timestamp=datetime.now(),
        domain=domain,
        question=question,
        facts=facts,
        gaps=gaps,
        scenarios=[
            {
                "id": "s1",
                "description": f"Optimista {domain}: {question}",
                "outcome": "positivo",
                "probability": 0.6
            },
            {
                "id": "s2",
                "description": f"Conservador {domain}: {question}",
                "outcome": "neutral",
                "probability": 0.4
            }
        ],
        risks={"volatilidad": 0.3, "incertidumbre": 0.5},
        assumptions=["Mercado estable", "Datos precisos"],
        llm_insight=llm_insight,
        llm_explanation=llm_explanation,
        confidence=exploration.get("confidence", 0.7),
        risk_level="medium",
        memory_influence=None,
        similar_cases=[],
        prediction="proceed"
    ).model_dump()
    data["exploration_confidence"] = exploration.get("confidence", 0.5)
    data["llm_calls"] = llm_calls  # ACO metric
    return data

