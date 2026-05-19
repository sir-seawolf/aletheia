"""
Simulator — DecisionReport generation for the v1 cognitive pipeline.

Responsibility: generate scenarios, risks, assumptions from exploration output via LLM.
Falls back to placeholder scenarios if LLM JSON parse fails.
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, Optional

from core.schemas.decision_contract import DecisionReport
from core.llm import router
from ai.prompts import simulation_prompt, insight_prompt


def run(
    exploration: Dict[str, Any],
    policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    domain   = exploration.get("domain", "unknown")
    question = exploration.get("question", "unknown")
    facts    = exploration.get("facts", [])
    gaps     = exploration.get("gaps", [])
    temp     = policy.get("temperature", 0.3) if policy else 0.3

    context_dict = {
        "domain": domain, "question": question,
        "risk": {"level": "medium", "require_scenarios": True},
        "user_profile_str": exploration.get("user_profile_str", ""),
    }

    sim_prompt    = simulation_prompt(context_dict, exploration)
    sim_response  = router.generate(task="simulation", prompt=sim_prompt,
                                    context={"domain": domain}, temp=temp)
    llm_calls = 1

    scenarios, risks, assumptions = _parse_simulation(sim_response, domain, question)

    risk_list   = risks if isinstance(risks, list) else list(risks.keys())
    ins_prompt  = insight_prompt(context_dict, scenarios, risk_list, assumptions)
    ins_response = router.generate(task="insight", prompt=ins_prompt,
                                   context={"domain": domain}, temp=temp)
    llm_calls += 1

    llm_insight = _parse_insight(ins_response)

    data = DecisionReport(
        timestamp=datetime.now(),
        domain=domain,
        question=question,
        facts=facts,
        gaps=gaps,
        scenarios=scenarios,
        risks=risks if isinstance(risks, dict) else {r: 0.5 for r in risks},
        assumptions=assumptions,
        llm_insight=llm_insight,
        llm_explanation=sim_response[:500] if sim_response else "",
        confidence=exploration.get("confidence", 0.7),
        risk_level="medium",
        memory_influence=None,
        similar_cases=[],
        prediction="proceed",
    ).model_dump(mode="json")

    data["exploration_confidence"] = exploration.get("confidence", 0.5)
    data["llm_calls"]              = llm_calls
    data["user_profile_str"]       = exploration.get("user_profile_str", "")
    return data


def _parse_simulation(response: str, domain: str, question: str):
    if response:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = "\n".join(l for l in cleaned.splitlines() if not l.startswith("```")).strip()
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict) and "scenarios" in data:
                return data.get("scenarios", []), data.get("risks", []), data.get("assumptions", [])
        except ValueError:
            pass
        m = re.search(r'\{[^{}]*"scenarios".*?\}', cleaned, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group())
                return data.get("scenarios", []), data.get("risks", []), data.get("assumptions", [])
            except ValueError:
                pass

    scenarios = [
        {"id": "s1", "type": "optimista",
         "description": f"Escenario favorable en {domain}: el plan avanza con buenos resultados y sin obstáculos mayores.",
         "outcome": "positivo",  "probability": 0.55},
        {"id": "s2", "type": "conservador",
         "description": f"Escenario cauto en {domain}: progreso gradual con ajustes necesarios en el camino.",
         "outcome": "neutral",   "probability": 0.35},
        {"id": "s3", "type": "pesimista",
         "description": f"Escenario adverso en {domain}: obstáculos significativos que exigen replantear la estrategia.",
         "outcome": "negativo",  "probability": 0.10},
    ]
    return scenarios, ["Incertidumbre en los datos disponibles"], ["Condiciones del entorno relativamente estables"]


def _parse_insight(response: str) -> str:
    if not response:
        return ""
    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = "\n".join(l for l in cleaned.splitlines() if not l.startswith("```")).strip()
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data.get("insight", cleaned)
    except ValueError:
        pass
    m = re.search(r'"insight"\s*:\s*"([^"]+)"', cleaned)
    if m:
        return m.group(1)
    return cleaned


def _build_scenario_description(scenario_type: str, domain: str) -> str:
    """Build a generic scenario description. Kept for test compatibility."""
    descriptions = {
        "optimista":   f"Escenario favorable en {domain}: resultados positivos sin obstáculos mayores.",
        "conservador": f"Escenario cauto en {domain}: progreso gradual con ajustes necesarios.",
        "pesimista":   f"Escenario adverso en {domain}: obstáculos que exigen replantear la estrategia.",
    }
    return descriptions.get(scenario_type, f"Escenario {scenario_type} en {domain}.")
