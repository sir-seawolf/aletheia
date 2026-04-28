"""Simulator - DecisionReport Generator with Router (LLMRouter integrated)"""

from typing import Dict, Any, List
from core.schemas.decision_contract import DecisionReport
from core.llm.router import generate as llm_generate
from datetime import datetime

def run(exploration: Dict[str, Any]) -> Dict[str, Any]:
    \"\"\"
    Genera escenarios, riesgos, supuestos desde exploration.
    LLM via router.enrich in orchestrator.
    \"\"\"
    domain = exploration.get("domain", "unknown")
    question = exploration.get("question", "unknown")
    facts = exploration.get("facts", [])
    gaps = exploration.get("gaps", [])

    # LLM via orchestrator.router.enrich("simulation", simulation)
    explain_prompt = f"Provide detailed explanation for {domain} {question}. Facts: {facts}. Gaps: {gaps}."
    llm_explanation = llm_generate(explain_prompt, domain=domain, task="simulator", temperature=0.3)

    insight_prompt = f"Summarize insight for {domain}: {question}. Bias?"
    llm_insight = llm_generate(insight_prompt, domain=domain, task="simulator", temperature=0.2)

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
    return data

