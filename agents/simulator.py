"""
Simulator Agent - DecisionReport generation using LLMRouter.

STATUS: IMPLEMENTED (production v1.1)
Dependencies: core.llm.router, core.schemas.decision_contract, ai.prompts
Last stable version: v1.2

Responsibility: Generate scenarios, risks, assumptions from exploration via LLM.
Falls back to placeholder scenarios if LLM JSON parse fails.
"""

import json
import re
from typing import Dict, Any, Optional
from core.schemas.decision_contract import DecisionReport
from core.llm import router
from ai.prompts import simulation_prompt, insight_prompt
from datetime import datetime


def run(exploration: Dict[str, Any], policy: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate DecisionReport from exploration facts/gaps using LLM.

    Args:
        exploration (dict): Explorer output with facts/gaps/confidence
        policy (dict, optional): ACO policy for temperature

    Returns:
        dict: DecisionReport with scenarios, risks, assumptions, llm_insight
    """
    domain   = exploration.get("domain", "unknown")
    question = exploration.get("question", "unknown")
    facts    = exploration.get("facts", [])
    gaps     = exploration.get("gaps", [])
    temp     = policy.get("temperature", 0.3) if policy else 0.3

    context_dict = {
        "domain": domain,
        "question": question,
        "risk": {"level": "medium", "require_scenarios": True},
        "user_profile_str": exploration.get("user_profile_str", ""),
    }

    # --- Generate scenarios via LLM ---
    sim_prompt = simulation_prompt(context_dict, exploration)
    sim_response = router.generate(task="simulation", prompt=sim_prompt, context={"domain": domain}, temp=temp)
    llm_calls = 1

    scenarios, risks, assumptions = _parse_simulation(sim_response, domain, question)

    # --- Generate insight via LLM ---
    risk_list = risks if isinstance(risks, list) else list(risks.keys())
    ins_prompt = insight_prompt(context_dict, scenarios, risk_list, assumptions)
    insight_response = router.generate(task="insight", prompt=ins_prompt, context={"domain": domain}, temp=temp)
    llm_calls += 1

    llm_insight = _parse_insight(insight_response)

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
        prediction="proceed"
    ).model_dump()

    data["exploration_confidence"] = exploration.get("confidence", 0.5)
    data["llm_calls"] = llm_calls
    data["user_profile_str"] = exploration.get("user_profile_str", "")
    return data


def _parse_simulation(response: str, domain: str, question: str):
    """
    Parse LLM simulation response. Returns (scenarios, risks, assumptions).
    Falls back to generic placeholders if JSON is invalid.
    """
    if response:
        cleaned = response.strip()
        if cleaned.startswith("```"):
            cleaned = "\n".join(l for l in cleaned.splitlines() if not l.startswith("```")).strip()

        # Try direct parse
        try:
            data = json.loads(cleaned)
            if isinstance(data, dict) and "scenarios" in data:
                return (
                    data.get("scenarios", []),
                    data.get("risks", []),
                    data.get("assumptions", []),
                )
        except ValueError:
            pass

        # Regex: find JSON block
        m = re.search(r'\{[^{}]*"scenarios".*?\}', cleaned, re.DOTALL)
        if m:
            try:
                data = json.loads(m.group())
                return (
                    data.get("scenarios", []),
                    data.get("risks", []),
                    data.get("assumptions", []),
                )
            except ValueError:
                pass

    # Fallback: generic scenarios (LLM did not return valid JSON)
    scenarios = [
        {"id": "s1", "type": "optimista",   "description": f"Escenario favorable en {domain}: el plan avanza con buenos resultados y sin obstáculos mayores.",          "outcome": "positivo",  "probability": 0.55},
        {"id": "s2", "type": "conservador", "description": f"Escenario cauto en {domain}: progreso gradual con ajustes necesarios en el camino.",                       "outcome": "neutral",   "probability": 0.35},
        {"id": "s3", "type": "pesimista",   "description": f"Escenario adverso en {domain}: obstáculos significativos que exigen replantear la estrategia.",            "outcome": "negativo",  "probability": 0.10},
    ]
    return scenarios, ["Incertidumbre en los datos disponibles"], ["Condiciones del entorno relativamente estables"]


def _parse_insight(response: str) -> str:
    """
    Parse insight response — returns clean string.
    Tries JSON extraction first (for structured insight field), then returns raw text.
    """
    if not response:
        return ""

    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = "\n".join(l for l in cleaned.splitlines() if not l.startswith("```")).strip()

    # Try JSON insight field
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
